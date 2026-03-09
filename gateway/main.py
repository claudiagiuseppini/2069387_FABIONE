import json
import asyncio
import time
import threading
import requests
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from contextlib import asynccontextmanager

# Import dai moduli locali
from config import SIMULATOR_URL, DEFAULT_RULES_FILE, DEFAULT_ACTUATORS
from models import RuleCreate, RuleUpdate, ActuatorCommand
from state import (
    latest_state, event_log, actuators_state, 
    state_lock, event_lock, actuator_lock
)
from database import get_db_connection
from workers import stomp_worker, poll_actuators, stomp_conn, add_event

# --- Utility Functions ---

def load_default_rules():
    try:
        with DEFAULT_RULES_FILE.open("r", encoding="utf-8") as handle:
            return json.load(handle)
    except Exception as e:
        print(f"❌ Errore critico: Impossibile leggere {DEFAULT_RULES_FILE}: {e}")
        return []

def build_dashboard_snapshot():
    with state_lock:
        latest = list(latest_state.values())
    with actuator_lock:
        # Se la cache è vuota, usa i default per non rompere la UI
        actuators = actuators_state if actuators_state else dict(DEFAULT_ACTUATORS)
    with event_lock:
        events = list(event_log)
        
    return {
        "latest": latest,
        "actuators": actuators,
        "health": {
            "status": True,
            "broker_connected": stomp_conn.is_connected(),
            "cached_metrics": len(latest),
            "cached_events": len(events),
            "known_actuators": len(actuators)
        },
        "timestamp": time.strftime("%Y-%m-%d %H:%M:%S")
    }

# --- Lifecycle Management ---

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Avvio dei thread di background
    t1 = threading.Thread(target=stomp_worker, daemon=True)
    t2 = threading.Thread(target=poll_actuators, daemon=True)
    t1.start()
    t2.start()
    yield
    # Shutdown
    if stomp_conn.is_connected():
        stomp_conn.disconnect()

app = FastAPI(title="Mars IoT Backend", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# --- ENDPOINT SYSTEM & HEALTH ---

@app.get("/api/health")
def health():
    return {
        "status": True,
        "broker_connected": stomp_conn.is_connected(),
        "cached_metrics": len(latest_state),
        "cached_events": len(event_log),
        "known_actuators": len(actuators_state)
    }

@app.get("/api/stream/dashboard")
async def stream_dashboard():
    async def event_generator():
        last_payload = ""
        heartbeat_seconds = 15
        elapsed = 0
        yield "retry: 5000\n\n"

        while True:
            snapshot = build_dashboard_snapshot()
            payload = json.dumps(snapshot, ensure_ascii=True, sort_keys=True)

            if payload != last_payload:
                last_payload = payload
                elapsed = 0
                yield f"data: {payload}\n\n"
            else:
                elapsed += 1
                if elapsed >= heartbeat_seconds:
                    elapsed = 0
                    yield ": ping\n\n"
            await asyncio.sleep(1)

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no"
        }
    )

# --- ENDPOINT SENSORI ---

@app.get("/api/latest")
def get_latest():
    with state_lock:
        return list(latest_state.values())

@app.get("/api/latest/{sensor_id}")
def get_latest_by_sensor(sensor_id: str):
    with state_lock:
        return [v for v in latest_state.values() if v.get("sensor_id") == sensor_id]

@app.get("/api/events")
def get_events():
    with event_lock:
        return {"items": event_log}

# --- ENDPOINT ATTUATORI ---

@app.get("/api/actuators")
def get_actuators():
    with actuator_lock:
        if not actuators_state:
            return dict(DEFAULT_ACTUATORS)
        return actuators_state

@app.post("/api/actuators/reset")
def reset_all_actuators_to_default():
    with actuator_lock:
        known_actuators = set(DEFAULT_ACTUATORS.keys()) | set(actuators_state.keys())
    
    if not known_actuators:
        known_actuators = set(DEFAULT_ACTUATORS.keys())

    errors = []
    for aid in sorted(known_actuators):
        try:
            r = requests.post(f"{SIMULATOR_URL}/api/actuators/{aid}", json={"state": "OFF"}, timeout=5)
            if r.status_code not in (200, 201):
                errors.append(f"{aid}: HTTP {r.status_code}")
        except Exception as e:
            errors.append(f"{aid}: {e}")

    with actuator_lock:
        for aid in known_actuators:
            actuators_state[aid] = "OFF"

    if errors:
        add_event(f"Reset attuatori con errori ({len(errors)})", "warning")
        raise HTTPException(status_code=502, detail={"message": "Reset parziale", "errors": errors})

    add_event("Reset attuatori completato: tutti OFF", "warning")
    return {"ok": True, "reset_count": len(known_actuators), "state": "OFF"}

@app.post("/api/actuators/{actuator_id}")
def command_actuator(actuator_id: str, payload: ActuatorCommand):
    try:
        r = requests.post(f"{SIMULATOR_URL}/api/actuators/{actuator_id}", json={"state": payload.state}, timeout=5)
        if r.status_code not in (200, 201):
            raise HTTPException(status_code=r.status_code, detail=f"Errore simulatore: {r.text}")
        
        with actuator_lock:
            actuators_state[actuator_id] = payload.state
        
        add_event(f"Attuatore {actuator_id} impostato su {payload.state}", "success")
        return {"ok": True, "actuator_id": actuator_id, "state": payload.state}
    except HTTPException: raise
    except Exception as e: raise HTTPException(status_code=500, detail=str(e))

# --- ENDPOINT REGOLE (CRUD) ---

@app.get("/api/rules")
def get_rules():
    conn = get_db_connection()
    if not conn: raise HTTPException(status_code=500, detail="Connessione DB fallita")
    try:
        cursor = conn.cursor(dictionary=True)
        cursor.execute("SELECT id, sensor_name, metric_name, operator, threshold, actuator_name, action_value, enabled FROM automation_rules ORDER BY id DESC")
        rows = cursor.fetchall()
        cursor.close()
        return rows
    except Exception as e: raise HTTPException(status_code=500, detail=str(e))
    finally: conn.close()

@app.post("/api/rules")
def create_rule(rule: RuleCreate):
    conn = get_db_connection()
    if not conn: raise HTTPException(status_code=500, detail="Connessione DB fallita")
    try:
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO automation_rules (sensor_name, metric_name, operator, threshold, actuator_name, action_value, enabled)
            VALUES (%s, %s, %s, %s, %s, %s, %s)
        """, (rule.sensor_name, rule.metric_name, rule.operator, rule.threshold, rule.actuator_name, rule.action_value, int(rule.enabled)))
        conn.commit()
        rid = cursor.lastrowid
        cursor.close()
        add_event(f"Creata regola {rid} per {rule.sensor_name}.{rule.metric_name}", "success")
        return {"ok": True, "id": rid}
    except Exception as e: raise HTTPException(status_code=500, detail=str(e))
    finally: conn.close()

@app.put("/api/rules/{rule_id}")
def update_rule(rule_id: int, rule: RuleUpdate):
    conn = get_db_connection()
    if not conn: raise HTTPException(status_code=500, detail="Connessione DB fallita")
    try:
        payload = rule.model_dump(exclude_unset=True)
        fields, values = [], []
        for key, value in payload.items():
            if key == "enabled": value = int(value)
            fields.append(f"{key} = %s")
            values.append(value)
        
        if not fields: raise HTTPException(status_code=400, detail="Nessun campo da aggiornare")
        values.append(rule_id)
        
        cursor = conn.cursor()
        cursor.execute(f"UPDATE automation_rules SET {', '.join(fields)} WHERE id = %s", tuple(values))
        conn.commit()
        cursor.close()
        add_event(f"Aggiornata regola {rule_id}", "warning")
        return {"ok": True, "id": rule_id}
    except HTTPException: raise
    except Exception as e: raise HTTPException(status_code=500, detail=str(e))
    finally: conn.close()

@app.delete("/api/rules/{rule_id}")
def delete_rule(rule_id: int):
    conn = get_db_connection()
    if not conn: raise HTTPException(status_code=500, detail="Connessione DB fallita")
    try:
        cursor = conn.cursor()
        cursor.execute("DELETE FROM automation_rules WHERE id = %s", (rule_id,))
        conn.commit()
        cursor.close()
        add_event(f"Eliminata regola {rule_id}", "danger")
        return {"ok": True, "id": rule_id}
    except Exception as e: raise HTTPException(status_code=500, detail=str(e))
    finally: conn.close()

@app.post("/api/rules/reset")
def reset_rules_to_default():
    default_rules = load_default_rules()
    conn = get_db_connection()
    if not conn: raise HTTPException(status_code=500, detail="Connessione DB fallita")
    try:
        cursor = conn.cursor()
        cursor.execute("TRUNCATE TABLE automation_rules")
        cursor.executemany("""
            INSERT INTO automation_rules (id, sensor_name, metric_name, operator, threshold, actuator_name, action_value, enabled)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
        """, [(idx, r["sensor_name"], r["metric_name"], r["operator"], r["threshold"], r["actuator_name"], r["action_value"], int(r["enabled"])) 
              for idx, r in enumerate(default_rules, start=1)])
        conn.commit()
        cursor.close()
        add_event(f"Reset regole completato: {len(default_rules)} ripristinate", "warning")
        return {"ok": True, "reset_count": len(default_rules)}
    except Exception as e:
        conn.rollback()
        raise HTTPException(status_code=500, detail=str(e))
    finally: conn.close()
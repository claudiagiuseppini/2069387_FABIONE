import json
import asyncio
import time
import threading
import requests
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from contextlib import asynccontextmanager

from config import SIMULATOR_URL, DEFAULT_RULES_FILE, DEFAULT_ACTUATORS
from models import RuleCreate, RuleUpdate, ActuatorCommand
from state import latest_state, event_log, actuators_state, state_lock, event_lock, actuator_lock
from database import get_db_connection
from workers import stomp_worker, poll_actuators, stomp_conn, add_event

# --- Utility Snapshot (CORRETTA) ---
def build_dashboard_snapshot():
    with state_lock:
        latest = list(latest_state.values())
    with actuator_lock:
        actuators = dict(actuators_state)
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
            "known_actuators": len(actuators) # <--- Fondamentale per il frontend
        },
        "timestamp": time.strftime("%Y-%m-%d %H:%M:%S")
    }

@asynccontextmanager
async def lifespan(app: FastAPI):
    t1 = threading.Thread(target=stomp_worker, daemon=True)
    t2 = threading.Thread(target=poll_actuators, daemon=True)
    t1.start()
    t2.start()
    yield
    if stomp_conn.is_connected(): stomp_conn.disconnect()

app = FastAPI(title="Mars Backend API", lifespan=lifespan)
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_credentials=True, allow_methods=["*"], allow_headers=["*"])

# --- ROTTE API ---

@app.get("/api/health")
def health():
    return {"status": True, "broker_connected": stomp_conn.is_connected()}

@app.get("/api/stream/dashboard")
async def stream_dashboard():
    async def event_generator():
        yield "retry: 5000\n\n"
        last_payload = ""
        while True:
            snapshot = build_dashboard_snapshot()
            payload = json.dumps(snapshot, sort_keys=True)
            if payload != last_payload:
                last_payload = payload
                yield f"data: {payload}\n\n"
            await asyncio.sleep(1)
    return StreamingResponse(event_generator(), media_type="text/event-stream")

@app.get("/api/actuators")
def get_actuators():
    with actuator_lock:
        return actuators_state if actuators_state else dict(DEFAULT_ACTUATORS)

@app.post("/api/actuators/{actuator_id}")
def command_actuator(actuator_id: str, payload: ActuatorCommand):
    try:
        # 1. Invia il comando al simulatore
        r = requests.post(f"{SIMULATOR_URL}/api/actuators/{actuator_id}", 
                          json={"state": payload.state}, timeout=5)
        
        if r.status_code not in (200, 201):
            raise HTTPException(status_code=r.status_code, detail=f"Simulatore errore: {r.text}")
        
        # 2. Aggiorna lo stato locale SOLO se il simulatore ha risposto OK
        with actuator_lock:
            actuators_state[actuator_id] = payload.state
        
        add_event(f"Attuatore {actuator_id} -> {payload.state}", "success")
        return {"ok": True, "state": payload.state}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# --- CRUD REGOLE ---

@app.get("/api/rules")
def get_rules():
    conn = get_db_connection()
    if not conn: raise HTTPException(status_code=500)
    cursor = conn.cursor(dictionary=True)
    cursor.execute("SELECT * FROM automation_rules ORDER BY id DESC")
    rows = cursor.fetchall()
    cursor.close()
    conn.close()
    return rows

@app.post("/api/rules")
def create_rule(rule: RuleCreate):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO automation_rules (sensor_name, metric_name, operator, threshold, actuator_name, action_value, enabled)
        VALUES (%s, %s, %s, %s, %s, %s, %s)
    """, (rule.sensor_name, rule.metric_name, rule.operator, rule.threshold, rule.actuator_name, rule.action_value, int(rule.enabled)))
    conn.commit()
    rid = cursor.lastrowid
    cursor.close()
    conn.close()
    add_event(f"Creata regola {rid}", "success")
    return {"ok": True, "id": rid}

@app.put("/api/rules/{rule_id}")
def update_rule(rule_id: int, rule: RuleUpdate):
    conn = get_db_connection()
    payload = rule.model_dump(exclude_unset=True)
    if not payload: raise HTTPException(status_code=400)
    
    fields = [f"{k} = %s" for k in payload.keys()]
    values = list(payload.values())
    values.append(rule_id)
    
    cursor = conn.cursor()
    cursor.execute(f"UPDATE automation_rules SET {', '.join(fields)} WHERE id = %s", tuple(values))
    conn.commit()
    cursor.close()
    conn.close()
    return {"ok": True}

@app.delete("/api/rules/{rule_id}")
def delete_rule(rule_id: int):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM automation_rules WHERE id = %s", (rule_id,))
    conn.commit()
    cursor.close()
    conn.close()
    add_event(f"Eliminata regola {rule_id}", "danger")
    return {"ok": True}

@app.post("/api/rules/reset")
def reset_rules_to_default():
    defaults = load_default_rules()
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("TRUNCATE TABLE automation_rules")
    for idx, r in enumerate(defaults, 1):
        cursor.execute("""
            INSERT INTO automation_rules (id, sensor_name, metric_name, operator, threshold, actuator_name, action_value, enabled)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
        """, (idx, r["sensor_name"], r["metric_name"], r["operator"], r["threshold"], r["actuator_name"], r["action_value"], int(r["enabled"])))
    conn.commit()
    cursor.close()
    conn.close()
    add_event("Reset regole completato", "warning")
    return {"ok": True, "count": len(defaults)}
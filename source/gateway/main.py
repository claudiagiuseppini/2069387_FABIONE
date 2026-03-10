import json
import asyncio
import time
import threading
import requests
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from contextlib import asynccontextmanager

# Import from local modules
from config import SIMULATOR_URL, DEFAULT_RULES_FILE, DEFAULT_ACTUATORS
from models import RuleCreate, RuleUpdate, ActuatorCommand
from state import (
    latest_state, event_log, actuators_state, 
    state_lock, event_lock, actuator_lock
)
from database import get_db_connection
from workers import stomp_worker, poll_actuators, stomp_conn, add_event

#UTILITY FUNCTIONS

def load_default_rules():
    '''open file with default rules, reads it and return the contents'''
    try:
        with DEFAULT_RULES_FILE.open("r", encoding="utf-8") as handle:
            return json.load(handle)
    except Exception as e:
        print(f"❌ Critical error: Failed to read {DEFAULT_RULES_FILE}: {e}")
        return []

def build_dashboard_snapshot():
    '''collects and aggregates data for the dashboard in a single object that the function returns'''
    with state_lock:
        latest = list(latest_state.values())
    with actuator_lock:
        # If the cache is empty, it uses the default
        actuators = actuators_state if actuators_state else dict(DEFAULT_ACTUATORS)
    with event_lock:
        events = list(event_log)
    
    # returns a single object with all data
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

# LIFECYCLE MANAGEMENT

@asynccontextmanager
async def lifespan(app: FastAPI):
    '''Manages lifetime events for the service, starting startup events and shutdown operations'''
    # Starting background thread operations
    t1 = threading.Thread(target=stomp_worker, daemon=True)
    t2 = threading.Thread(target=poll_actuators, daemon=True)
    t1.start()
    t2.start()
    yield
    # Shutdown connection closing
    if stomp_conn.is_connected():
        stomp_conn.disconnect()

# Fastapi definition
app = FastAPI(title="Mars IoT Backend", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ENDPOINTS

@app.get("/api/health")
def health():
    '''returns the health status of the service'''
    return {
        "status": True,
        "broker_connected": stomp_conn.is_connected(),
        "cached_metrics": len(latest_state),
        "cached_events": len(event_log),
        "known_actuators": len(actuators_state)
    }

@app.get("/api/stream/dashboard")
async def stream_dashboard():
    '''SSE endpoint that keeps an open connection with frontend.
    It sends updates too the dashboard when data changes'''
    async def event_generator():
        # initialized variables
        last_payload = ""
        heartbeat_seconds = 15
        elapsed = 0

        # SSE instruction too make browser reconnect
        yield "retry: 5000\n\n"

        while True:
            # gets current dashboard state
            snapshot = build_dashboard_snapshot()
            payload = json.dumps(snapshot, ensure_ascii=True, sort_keys=True)

            # updates state if there's some difference, otherwise sends a ping message to keep the connection open
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

    # return a StreamingResponse class 
    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no"
        }
    )

# --- ENDPOINT SENSORS ---

@app.get("/api/latest")
def get_latest():
    '''return latest state list'''
    with state_lock:
        return list(latest_state.values())

@app.get("/api/latest/{sensor_id}")
def get_latest_by_sensor(sensor_id: str):
    '''return latest value for selected sensor'''
    with state_lock:
        return [v for v in latest_state.values() if v.get("sensor_id") == sensor_id]

@app.get("/api/events")
def get_events():
    '''return events log'''
    with event_lock:
        return {"items": event_log}

# --- ENDPOINT ACTUATORS ---

@app.get("/api/actuators")
def get_actuators():
    '''returns actuators list'''
    with actuator_lock:
        if not actuators_state:
            return dict(DEFAULT_ACTUATORS)
        return actuators_state

@app.post("/api/actuators/reset")
def reset_all_actuators_to_default():
    '''sets all actuatorss back to default (OFF)'''

    # get actuators list
    with actuator_lock:
        known_actuators = set(DEFAULT_ACTUATORS.keys()) | set(actuators_state.keys())
    
    if not known_actuators:
        known_actuators = set(DEFAULT_ACTUATORS.keys())

    # sends to the simulator, for each actuator, a message to set it to OFF
    errors = []
    for aid in sorted(known_actuators):
        try:
            r = requests.post(f"{SIMULATOR_URL}/api/actuators/{aid}", json={"state": "OFF"}, timeout=5)
            if r.status_code not in (200, 201):
                errors.append(f"{aid}: HTTP {r.status_code}")
        except Exception as e:
            errors.append(f"{aid}: {e}")

    # set local state for actuators to OFF
    with actuator_lock:
        for aid in known_actuators:
            actuators_state[aid] = "OFF"

    # record possible errors to be displayed in the dashboard
    if errors:
        add_event(f"Reset actuators with errors ({len(errors)})", "warning")
        raise HTTPException(status_code=502, detail={"message": "partial errors", "errors": errors})

    # record the event in case of success
    add_event("Reset actuators completed: all OFF", "warning")
    return {"ok": True, "reset_count": len(known_actuators), "state": "OFF"}

@app.post("/api/actuators/{actuator_id}")
def command_actuator(actuator_id: str, payload: ActuatorCommand):
    '''send a state update to a specific actuator'''
    try:
        # send message to simulator API to update state of a specific actuator
        r = requests.post(f"{SIMULATOR_URL}/api/actuators/{actuator_id}", json={"state": payload.state}, timeout=5)
        if r.status_code not in (200, 201):
            raise HTTPException(status_code=r.status_code, detail=f"Simulator error: {r.text}")
        
        # update actuator state in internal memory
        with actuator_lock:
            actuators_state[actuator_id] = payload.state
        
        # add event to logs
        add_event(f"Actuator {actuator_id} set to {payload.state}", "success")
        return {"ok": True, "actuator_id": actuator_id, "state": payload.state}
    except HTTPException: raise
    except Exception as e: raise HTTPException(status_code=500, detail=str(e))

# ENDPOINT RULES

@app.get("/api/rules")
def get_rules():
    '''Interrogates database to obtain required rules and returns them'''

    # open database connection
    conn = get_db_connection()
    if not conn: raise HTTPException(status_code=500, detail="failed db connection")
    try:
        # sends to database a query to get all the rules and return them
        cursor = conn.cursor(dictionary=True)
        cursor.execute("SELECT id, sensor_name, metric_name, operator, threshold, actuator_name, action_value, enabled FROM automation_rules ORDER BY id DESC")
        rows = cursor.fetchall()
        cursor.close()
        return rows
    except Exception as e: raise HTTPException(status_code=500, detail=str(e))
    finally: conn.close()

@app.post("/api/rules")
def create_rule(rule: RuleCreate):
    '''inserts a new rule received as an argument in the database'''

    # open a db connection
    conn = get_db_connection()
    if not conn: raise HTTPException(status_code=500, detail="failed db connection")
    try:
        # sends a query to the database to insert the new rule
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO automation_rules (sensor_name, metric_name, operator, threshold, actuator_name, action_value, enabled)
            VALUES (%s, %s, %s, %s, %s, %s, %s)
        """, (rule.sensor_name, rule.metric_name, rule.operator, rule.threshold, rule.actuator_name, rule.action_value, int(rule.enabled)))
        conn.commit()
        rid = cursor.lastrowid
        cursor.close()
        
        #add the rule insertion to the events
        add_event(f"Created rule {rid} for {rule.sensor_name}.{rule.metric_name}", "success")
        return {"ok": True, "id": rid}
    except Exception as e: raise HTTPException(status_code=500, detail=str(e))
    finally: conn.close()

@app.put("/api/rules/{rule_id}")
def update_rule(rule_id: int, rule: RuleUpdate):
    '''ask the database to update a rule'''

    # open a connection to the database
    conn = get_db_connection()
    if not conn: raise HTTPException(status_code=500, detail="failed db connection")
    try:
        # constructs the payload to send to the database
        payload = rule.model_dump(exclude_unset=True)
        fields, values = [], []
        for key, value in payload.items():
            if key == "enabled": value = int(value)
            fields.append(f"{key} = %s")
            values.append(value)
        
        # case in which there's no update
        if not fields: raise HTTPException(status_code=400, detail="No field to update")
        values.append(rule_id)
        
        # sends the query to the db with the changes
        cursor = conn.cursor()
        cursor.execute(f"UPDATE automation_rules SET {', '.join(fields)} WHERE id = %s", tuple(values))
        conn.commit()
        cursor.close()
        
        # adds the database insertion to the events
        add_event(f"Updated rule {rule_id}", "warning")
        return {"ok": True, "id": rule_id}
    except HTTPException: raise
    except Exception as e: raise HTTPException(status_code=500, detail=str(e))
    finally: conn.close()

@app.delete("/api/rules/{rule_id}")
def delete_rule(rule_id: int):
    '''ask the database to delete a rule'''

    # open a connection to the database
    conn = get_db_connection()
    if not conn: raise HTTPException(status_code=500, detail="Connessione DB fallita")
    try:
        # sends to the database the query to delete the rule with the specified id
        cursor = conn.cursor()
        cursor.execute("DELETE FROM automation_rules WHERE id = %s", (rule_id,))
        conn.commit()
        cursor.close()

        # add the deletion to the events
        add_event(f"Rule eliminated {rule_id}", "danger")
        return {"ok": True, "id": rule_id}
    except Exception as e: raise HTTPException(status_code=500, detail=str(e))
    finally: conn.close()

@app.post("/api/rules/reset")
def reset_rules_to_default():
    '''sets all the rules to the inizial set'''

    #get initial set of rules and open a connection to the db
    default_rules = load_default_rules()
    conn = get_db_connection()
    if not conn: raise HTTPException(status_code=500, detail="failed db connection")
    try:
        # send to the db the query to reset the rules
        cursor = conn.cursor()
        cursor.execute("TRUNCATE TABLE automation_rules")
        cursor.executemany("""
            INSERT INTO automation_rules (id, sensor_name, metric_name, operator, threshold, actuator_name, action_value, enabled)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
        """, [(idx, r["sensor_name"], r["metric_name"], r["operator"], r["threshold"], r["actuator_name"], r["action_value"], int(r["enabled"])) 
              for idx, r in enumerate(default_rules, start=1)])
        conn.commit()
        cursor.close()

        # add the reset to the events log
        add_event(f"Rules reset completed: {len(default_rules)} restored", "warning")
        return {"ok": True, "reset_count": len(default_rules)}
    except Exception as e:
        conn.rollback()
        raise HTTPException(status_code=500, detail=str(e))
    finally: conn.close()
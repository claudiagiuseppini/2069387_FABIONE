import json
import time
import threading
from contextlib import asynccontextmanager
from typing import Optional

import requests
import stomp
import mysql.connector
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

BROKER_CONF = {
    "host": "broker",
    "port": 61613,
    "user": "admin",
    "pass": "admin_password"
}

DB_CONF = {
    "host": "db",
    "user": "user_mars",
    "password": "password_mars",
    "database": "mars_iot"
}

SIMULATOR_URL = "http://simulator:8080"

latest_state = {}
event_log = []
actuators_state = {
    "cooling_fan": "OFF",
    "entrance_humidifier": "OFF",
    "hall_ventilation": "OFF",
    "habitat_heater": "OFF"
}

state_lock = threading.Lock()
event_lock = threading.Lock()
actuator_lock = threading.Lock()

stomp_conn = stomp.Connection([(BROKER_CONF["host"], BROKER_CONF["port"])])


class RuleCreate(BaseModel):
    sensor_name: str
    metric_name: str
    operator: str
    threshold: float
    actuator_name: str
    action_value: str
    enabled: bool = True


class RuleUpdate(BaseModel):
    sensor_name: Optional[str] = None
    metric_name: Optional[str] = None
    operator: Optional[str] = None
    threshold: Optional[float] = None
    actuator_name: Optional[str] = None
    action_value: Optional[str] = None
    enabled: Optional[bool] = None


class ActuatorCommand(BaseModel):
    state: str


def get_db_connection():
    try:
        return mysql.connector.connect(**DB_CONF)
    except Exception as e:
        print(f"❌ Errore connessione DB: {e}", flush=True)
        return None


def add_event(message: str, event_type: str = "info"):
    with event_lock:
        event_log.insert(0, {
            "message": message,
            "type": event_type,
            "timestamp": time.strftime("%Y-%m-%d %H:%M:%S")
        })
        del event_log[50:]


class BackendStompListener(stomp.ConnectionListener):
    def on_message(self, frame):
        try:
            data = json.loads(frame.body)
            sensor_id = data.get("sensor_id", "unknown")
            
            # Recuperiamo la lista di metriche (ora al plurale 'metrics')
            metrics_list = data.get("metrics", [])

            # Se il sensore invia più metriche (es. temp e umidità), 
            # le salviamo singolarmente nel dizionario latest_state 
            # così il frontend può visualizzarle separatamente.
            with state_lock:
                for m_item in metrics_list:
                    metric_name = m_item.get("name", "unknown")
                    key = f"{sensor_id}.{metric_name}"
                    
                    # Creiamo un "flat object" compatibile con il frontend 
                    # che contiene i metadati del sensore e la singola metrica
                    flat_data = {
                        "sensor_id": sensor_id,
                        "sensor_type": data.get("sensor_type"),
                        "timestamp": data.get("timestamp"),
                        "status": data.get("status"),
                        "metric_name": metric_name,
                        "value": m_item.get("value"),
                        "unit": m_item.get("unit")
                    }
                    
                    latest_state[key] = flat_data

            add_event(f"Update: {sensor_id} ({len(metrics_list)} metriche)", "info")

        except Exception as e:
            print(f"⚠️ Errore parsing messaggio broker: {e}", flush=True)
    def on_error(self, frame):
        print(f"❌ Errore STOMP backend: {frame.body}", flush=True)

    def on_disconnected(self):
        print("🔄 Backend STOMP disconnesso", flush=True)


def connect_stomp():
    try:
        if not stomp_conn.is_connected():
            stomp_conn.set_listener("", BackendStompListener())
            stomp_conn.connect(
                BROKER_CONF["user"],
                BROKER_CONF["pass"],
                wait=True
            )
            stomp_conn.subscribe(
                destination="/topic/mars.#",
                id="backend_sub",
                ack="auto"
            )
            print("✅ Backend connesso al broker e sottoscritto a /topic/mars.#", flush=True)
    except Exception as e:
        print(f"❌ Errore connessione backend a broker: {e}", flush=True)


def stomp_worker():
    while True:
        try:
            if not stomp_conn.is_connected():
                connect_stomp()
        except Exception as e:
            print(f"⚠️ Worker STOMP: {e}", flush=True)
        time.sleep(5)


def poll_actuators():
    while True:
        try:
            response = requests.get(f"{SIMULATOR_URL}/api/actuators", timeout=5)
            if response.status_code == 200:
                payload = response.json()
                discovered = {}

                if isinstance(payload, dict):
                    if "actuators" in payload and isinstance(payload["actuators"], list):
                        for item in payload["actuators"]:
                            actuator_id = item.get("actuator_id") or item.get("id") or item.get("name")
                            state = item.get("state") or item.get("last_state") or "OFF"
                            if actuator_id:
                                discovered[actuator_id] = state
                    else:
                        for k, v in payload.items():
                            if isinstance(v, dict):
                                state = v.get("state") or v.get("last_state") or "OFF"
                                discovered[k] = state

                with actuator_lock:
                    actuators_state.clear()
                    actuators_state.update(discovered)

        except Exception as e:
            print(f"⚠️ Poll actuators error: {e}", flush=True)

        time.sleep(5)


@asynccontextmanager
async def lifespan(app: FastAPI):
    t1 = threading.Thread(target=stomp_worker, daemon=True)
    t2 = threading.Thread(target=poll_actuators, daemon=True)

    t1.start()
    t2.start()

    yield

    try:
        if stomp_conn.is_connected():
            stomp_conn.disconnect()
    except Exception:
        pass


app = FastAPI(title="Mars Backend API", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/api/health")
def health():
    return {
        "status": True,
        "broker_connected": stomp_conn.is_connected(),
        "cached_metrics": len(latest_state),
        "cached_events": len(event_log),
        "known_actuators": len(actuators_state)
    }


@app.get("/api/latest")
def get_latest():
    with state_lock:
        return list(latest_state.values())


@app.get("/api/latest/{sensor_id}")
def get_latest_by_sensor(sensor_id: str):
    with state_lock:
        filtered = [
            value for value in latest_state.values()
            if value.get("sensor_id") == sensor_id
        ]
    return filtered


@app.get("/api/events")
def get_events():
    with event_lock:
        return {"items": event_log}


@app.get("/api/actuators")
def get_actuators():
    with actuator_lock:
        if not actuators_state:
            return {
                "cooling_fan": "OFF",
                "entrance_humidifier": "OFF",
                "hall_ventilation": "OFF",
                "habitat_heater": "OFF"
            }
        return actuators_state


@app.post("/api/actuators/{actuator_id}")
def command_actuator(actuator_id: str, payload: ActuatorCommand):
    try:
        response = requests.post(
            f"{SIMULATOR_URL}/api/actuators/{actuator_id}",
            json={"state": payload.state},
            timeout=5
        )

        if response.status_code not in (200, 201):
            raise HTTPException(
                status_code=response.status_code,
                detail=f"Errore simulatore: {response.text}"
            )

        with actuator_lock:
            actuators_state[actuator_id] = payload.state

        add_event(f"Attuatore {actuator_id} impostato su {payload.state}", "success")

        return {
            "ok": True,
            "actuator_id": actuator_id,
            "state": payload.state
        }

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/rules")
def get_rules():
    conn = get_db_connection()
    if not conn:
        raise HTTPException(status_code=500, detail="Connessione DB fallita")

    try:
        cursor = conn.cursor(dictionary=True)
        cursor.execute("""
            SELECT id, sensor_name, metric_name, operator, threshold,
                   actuator_name, action_value, enabled
            FROM automation_rules
            ORDER BY id DESC
        """)
        rows = cursor.fetchall()
        cursor.close()
        return rows
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        conn.close()


@app.post("/api/rules")
def create_rule(rule: RuleCreate):
    conn = get_db_connection()
    if not conn:
        raise HTTPException(status_code=500, detail="Connessione DB fallita")

    try:
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO automation_rules
            (sensor_name, metric_name, operator, threshold, actuator_name, action_value, enabled)
            VALUES (%s, %s, %s, %s, %s, %s, %s)
        """, (
            rule.sensor_name,
            rule.metric_name,
            rule.operator,
            rule.threshold,
            rule.actuator_name,
            rule.action_value,
            int(rule.enabled)
        ))
        conn.commit()
        rule_id = cursor.lastrowid
        cursor.close()

        add_event(f"Creata regola {rule_id} per {rule.sensor_name}.{rule.metric_name}", "success")

        return {"ok": True, "id": rule_id}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        conn.close()


@app.put("/api/rules/{rule_id}")
def update_rule(rule_id: int, rule: RuleUpdate):
    conn = get_db_connection()
    if not conn:
        raise HTTPException(status_code=500, detail="Connessione DB fallita")

    try:
        fields = []
        values = []

        payload = rule.model_dump(exclude_unset=True)

        for key, value in payload.items():
            if key == "enabled":
                value = int(value)
            fields.append(f"{key} = %s")
            values.append(value)

        if not fields:
            raise HTTPException(status_code=400, detail="Nessun campo da aggiornare")

        values.append(rule_id)

        query = f"""
            UPDATE automation_rules
            SET {", ".join(fields)}
            WHERE id = %s
        """

        cursor = conn.cursor()
        cursor.execute(query, tuple(values))
        conn.commit()
        cursor.close()

        add_event(f"Aggiornata regola {rule_id}", "warning")

        return {"ok": True, "id": rule_id}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        conn.close()


@app.delete("/api/rules/{rule_id}")
def delete_rule(rule_id: int):
    conn = get_db_connection()
    if not conn:
        raise HTTPException(status_code=500, detail="Connessione DB fallita")

    try:
        cursor = conn.cursor()
        cursor.execute("DELETE FROM automation_rules WHERE id = %s", (rule_id,))
        conn.commit()
        cursor.close()

        add_event(f"Eliminata regola {rule_id}", "danger")

        return {"ok": True, "id": rule_id}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        conn.close()
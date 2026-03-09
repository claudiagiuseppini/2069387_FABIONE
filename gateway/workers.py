import json
import time
import requests
import stomp
from config import BROKER_CONF, SIMULATOR_URL
from state import (
    latest_state, event_log, actuators_state, 
    state_lock, event_lock, actuator_lock
)

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
            metrics_list = data.get("metrics", [])
            with state_lock:
                for m_item in metrics_list:
                    metric_name = m_item.get("name", "unknown")
                    key = f"{sensor_id}.{metric_name}"
                    latest_state[key] = {
                        "sensor_id": sensor_id,
                        "sensor_type": data.get("sensor_type"),
                        "timestamp": data.get("timestamp"),
                        "status": data.get("status"),
                        "metric_name": metric_name,
                        "value": m_item.get("value"),
                        "unit": m_item.get("unit"),
                        "source": data.get("source")
                    }
            add_event(f"Update: {sensor_id} ({len(metrics_list)} metriche)", "info")
        except Exception as e:
            print(f"⚠️ Errore parsing broker: {e}", flush=True)

    def on_error(self, frame): print(f"❌ Errore STOMP: {frame.body}", flush=True)
    def on_disconnected(self): print("🔄 STOMP disconnesso", flush=True)

stomp_conn = stomp.Connection([(BROKER_CONF["host"], BROKER_CONF["port"])])

def connect_stomp():
    try:
        if not stomp_conn.is_connected():
            stomp_conn.set_listener("", BackendStompListener())
            stomp_conn.connect(BROKER_CONF["user"], BROKER_CONF["pass"], wait=True)
            stomp_conn.subscribe(destination="/topic/mars.#", id="backend_sub", ack="auto")
    except Exception: pass

def stomp_worker():
    while True:
        if not stomp_conn.is_connected(): connect_stomp()
        time.sleep(5)

def poll_actuators():
    while True:
        try:
            response = requests.get(f"{SIMULATOR_URL}/api/actuators", timeout=5)
            if response.status_code == 200:
                payload = response.json()
                discovered = {}
                
                # --- LOGICA DI PARSING ORIGINALE (RIPRISTINATA) ---
                if isinstance(payload, dict):
                    if "actuators" in payload and isinstance(payload["actuators"], list):
                        for item in payload["actuators"]:
                            aid = item.get("actuator_id") or item.get("id") or item.get("name")
                            st = item.get("state") or item.get("last_state") or "OFF"
                            if aid: discovered[aid] = st
                    elif "actuators" in payload and isinstance(payload["actuators"], dict):
                        for aid, st in payload["actuators"].items():
                            discovered[aid] = st
                    else:
                        for k, v in payload.items():
                            if isinstance(v, dict):
                                st = v.get("state") or v.get("last_state") or "OFF"
                                discovered[k] = st
                
                with actuator_lock:
                    if discovered:
                        actuators_state.clear()
                        actuators_state.update(discovered)
        except Exception: pass
        time.sleep(5)
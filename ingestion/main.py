import requests
import time
import threading
import json
import stomp  # <--- Sostituito paho-mqtt con stomp.py
import sseclient 
from fastapi import FastAPI
from contextlib import asynccontextmanager

# Configurazione
SIMULATOR_URL = "http://simulator:8080"
BROKER_HOST = "broker"
BROKER_PORT = 61613  # <--- Porta standard STOMP per Artemis
BROKER_USER = "admin"
BROKER_PASS = "admin_password"

# Inizializzazione Client STOMP
stomp_conn_poll = stomp.Connection([(BROKER_HOST, BROKER_PORT)])
stomp_conn_telemetry = stomp.Connection([(BROKER_HOST, BROKER_PORT)])

def connect_stomp_generic(conn, label):
    """Gestisce la connessione per un client specifico."""
    try:
        if not conn.is_connected():
            conn.connect(BROKER_USER, BROKER_PASS, wait=True)
            print(f"✅ Connesso al Broker via STOMP ({label})", flush=True)
    except Exception as e:
        print(f"❌ Errore connessione STOMP ({label}): {e}", flush=True)

# --- FUNZIONI DI SUPPORTO (Invariate) ---

def normalize_to_metrics(sensor_id, raw_data):
    normalized_outputs = []
    timestamp = time.time()
    unit_generale = raw_data.get("unit", " ")

    def extract(data, prefix=""):
        if isinstance(data, dict):
            for key, value in data.items():
                if key in ["unit", "status", "timestamp", "sensor_id"]:
                    continue
                extract(value, f"{prefix}{key}" if not prefix else f"{prefix}_{key}")
        elif isinstance(data, list):
            for i, item in enumerate(data):
                extract(item, f"{prefix}_{i}")
        elif isinstance(data, (int, float)):
            normalized_outputs.append({
                "sensor_id": sensor_id,
                "timestamp": timestamp,
                "metric_name": prefix if prefix else "value",
                "value": float(data),
                "unit": unit_generale
            })
    extract(raw_data)
    return normalized_outputs

def get_sensors_list():
    try:
        response = requests.get(f"{SIMULATOR_URL}/api/sensors", timeout=10)
        if response.status_code == 200:
            return response.json().get("sensors", [])
    except Exception as e:
        print(f"Errore discovery sensori: {e}", flush=True)
    return ["greenhouse_temperature", "hydroponic_ph", "water_tank_level"]

# --- THREAD 1: POLLING SENSORI ---

def poll_sensors():
    active_sensors = get_sensors_list()
    while True:
        connect_stomp_generic(stomp_conn_poll, "POLLING") # Usa connessione poll
        for sensor in active_sensors:
            try:
                response = requests.get(f"{SIMULATOR_URL}/api/sensors/{sensor}", timeout=5)
                if response.status_code == 200:
                    metrics = normalize_to_metrics(sensor, response.json())
                    for metric in metrics:
                        topic = f"/topic/mars.metrics.{metric['sensor_id']}.{metric['metric_name']}"
                        # Invia tramite connessione poll
                        stomp_conn_poll.send(body=json.dumps(metric), destination=topic)
                        print(f"[POLL] {topic} -> {metric['value']}", flush=True)
                else:
                    print(f"Errore simulatore su {sensor}: {response.status_code}", flush=True)
            except Exception as e:
                print(f"Errore polling {sensor}: {e}", flush=True)
        time.sleep(5)

# --- THREAD 2: STREAMING TELEMETRIE ---

def get_telemetry_list():
    try:
        response = requests.get(f"{SIMULATOR_URL}/api/telemetry/topics", timeout=10)
        if response.status_code == 200:
            return response.json().get("topics", [])
    except Exception as e:
        print(f"Errore discovery telemetrie: {e}", flush=True)
    return []

def stream_telemetry(topic_id):
    stream_url = f"{SIMULATOR_URL}/api/telemetry/stream/{topic_id}" 
    print(f"Streaming TELEMETRIE (SSE) avviato su: {stream_url}", flush=True)
    while True:
        try:
            connect_stomp_generic(stomp_conn_telemetry, "TELEMETRY") # Usa connessione telemetria
            response = requests.get(stream_url, stream=True, timeout=None)
            client = sseclient.SSEClient(response)
            

            for event in client.events():
                if event.data:
                    raw_data = json.loads(event.data)

                    print(raw_data)
                    item_id = raw_data.get("id") or raw_data.get("sensor_id", "telemetry_unknown")
                    metrics = normalize_to_metrics(item_id, raw_data)
                    for metric in metrics:
                        topic = f"/topic/mars.telemetry.{metric['sensor_id']}.{metric['metric_name']}"
                        # Invia tramite connessione telemetria
                        stomp_conn_telemetry.send(body=json.dumps(metric), destination=topic)
                        print(f"[STREAM] {topic} -> {metric['value']}", flush=True)
        except Exception as e:
            print(f"Connessione SSE persa ({e}). Riconnessione in corso...", flush=True)
            time.sleep(5)

def cycle_telemetry():
    topic_list = get_telemetry_list()
    for topic in topic_list:
        t_topic = threading.Thread(target=stream_telemetry, args=(topic,), daemon=True)
        t_topic.start()
        time.sleep(2.0)
    
# --- FASTAPI SETUP ---

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Connettiamo inizialmente entrambi
    connect_stomp_generic(stomp_conn_poll, "POLLING")
    connect_stomp_generic(stomp_conn_telemetry, "TELEMETRY")

    t_sensors = threading.Thread(target=poll_sensors, daemon=True)
    t_telemetry = threading.Thread(target=cycle_telemetry, daemon=True)
    
    t_sensors.start()
    t_telemetry.start()
    
    yield
    
    # Cleanup di entrambe
    if stomp_conn_poll.is_connected():
        stomp_conn_poll.disconnect()
    if stomp_conn_telemetry.is_connected():
        stomp_conn_telemetry.disconnect()

app = FastAPI(lifespan=lifespan)

@app.get("/health")
def health():
    return {
        "status": "ingestion alive", 
        "broker_connected": stomp_conn.is_connected()
    }
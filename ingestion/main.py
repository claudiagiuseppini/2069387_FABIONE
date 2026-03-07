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

import datetime

def normalize_data(raw_data: dict) -> list:
    normalized_list = []
    
    # 1. Identificazione Metadati Comuni
    # sensor_id e sensor_type
    if "sensor_id" in raw_data:
        sensor_id = raw_data["sensor_id"]
        sensor_type = "sensor"
    elif "topic" in raw_data:
        # Rimuove "/topic/mars/" o "mars/telemetry/" se presente
        sensor_id = raw_data["topic"].replace("/topic/mars/", "").replace("mars/telemetry/", "")
        sensor_type = "telemetric"
    else:
        sensor_id = "unknown"
        sensor_type = "unknown"

    # Timestamp (conversione in integer unix timestamp)
    timestamp= raw_data.get("captured_at") or raw_data.get("event_time")
    
    # Status
    status = raw_data.get("status") or raw_data.get("last_state", "unknown")

    # Source (Peculiarità specifiche)
    source = None
    if "subsystem" in raw_data:
        source = raw_data["subsystem"]
    elif isinstance(raw_data.get("source"), dict):
        source = raw_data["source"].get("segment")
    elif "loop" in raw_data:
        source = raw_data["loop"]
    elif "airlock_id" in raw_data:
        source = raw_data["airlock_id"]

    # 2. Estrazione delle Metriche (Logica di branching basata sui pattern)
    metrics_to_process = [] # Lista di tuple (name, value, unit)

    # Caso A: Lista di measurements (Array di oggetti)
    if "measurements" in raw_data and isinstance(raw_data["measurements"], list):
        for m in raw_data["measurements"]:
            metrics_to_process.append((m.get("metric"), m.get("value"), m.get("unit")))

    # Caso B: Singola metrica esplicita (Campi 'metric', 'value', 'unit')
    elif "metric" in raw_data and "value" in raw_data:
        metrics_to_process.append((raw_data.get("metric"), raw_data.get("value"), raw_data.get("unit")))

    # Caso C: Metriche come nomi di campi (Peculiarità specifiche)
    else:
        # Definiamo i set di chiavi note che rappresentano metriche numeriche
        potential_metrics = [
            "pm1_ug_m3", "pm25_ug_m3", "pm10_ug_m3", 
            "level_pct", "level_liters",
            "power_kw", "voltage_v", "current_a", "cumulative_kwh",
            "temperature_c", "flow_l_min",
            "cycles_per_hour"
        ]
        for key in potential_metrics:
            if key in raw_data:
                metrics_to_process.append((key, raw_data[key], None))

    # 3. Costruzione dello Schema Unificato
    for name, val, unit in metrics_to_process:
        normalized_schema = {
            "sensor_id": sensor_id,
            "sensor_type": sensor_type,
            "timestamp": timestamp,
            "source": source,
            "status": status,
            "metric": {
                "name": name,
                "value": val,
                "unit": unit
            }
        }
        normalized_list.append(normalized_schema)

    print(normalized_list)
    return normalized_list

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
    print(f"🚀 Polling SENSORI avviato su: {active_sensors}", flush=True)
    
    while True:
        connect_stomp_generic(stomp_conn_poll, "POLLING")
        for sensor in active_sensors:
            try:
                response = requests.get(f"{SIMULATOR_URL}/api/sensors/{sensor}", timeout=5)
                if response.status_code == 200:
                    metrics = normalize_data(response.json())
                    
                    for m in metrics:

                        metric_name = m['metric']['name']
                        metric_value = m['metric']['value']
                        metric_unit = m['metric']['unit'] or ""

                        topic = f"/topic/mars.metrics.{m['sensor_id']}.{metric_name}"

                        stomp_conn_poll.send(body=json.dumps(m), destination=topic)
                        
                        print(f"[POLL] {topic} -> {metric_value} {metric_unit}", flush=True)
                else:
                    print(f"Errore simulatore su {sensor}: {response.status_code}", flush=True)
            except Exception as e:
                print(f"Errore durante il processing di {sensor}: {e}", flush=True)
        
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

                    metrics = normalize_data(raw_data)
                    for metric in metrics:
                        dest_topic = f"/topic/mars.telemetry.{metric['sensor_id']}.{metric['metric']['name']}"
                        stomp_conn_telemetry.send(body=json.dumps(metric), destination=dest_topic)
                        print(f"[STREAM] {dest_topic} -> {metric['metric']['value']} {metric['metric']['unit'] or ''}", flush=True)
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
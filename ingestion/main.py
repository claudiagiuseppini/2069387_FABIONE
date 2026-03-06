import requests
import time
import threading
import json
import paho.mqtt.client as mqtt
import sseclient  # <--- Nuova dipendenza per SSE
from fastapi import FastAPI
from contextlib import asynccontextmanager

# Configurazione
SIMULATOR_URL = "http://simulator:8080"
BROKER_HOST = "broker"
BROKER_PORT = 1883

# Inizializzazione Client MQTT
mqtt_client = mqtt.Client()
mqtt_client.username_pw_set("admin", "admin_password")

# --- FUNZIONI DI SUPPORTO (Invariate o ottimizzate) ---

def normalize_to_metrics(sensor_id, raw_data):
    """Analizza il JSON e produce una lista di metriche piatte."""
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
    """Discovery dinamica dei sensori (Polling mode)."""
    try:
        response = requests.get(f"{SIMULATOR_URL}/api/sensors", timeout=10)
        if response.status_code == 200:
            return response.json().get("sensors", [])
    except Exception as e:
        print(f"Errore discovery sensori: {e}", flush=True)
    return ["greenhouse_temperature", "hydroponic_ph", "water_tank_level"]

# --- THREAD 1: POLLING SENSORI (Il tuo codice originale) ---

def poll_sensors():
    active_sensors = get_sensors_list()
    print(f"Polling SENSORI avviato su: {active_sensors}", flush=True)
    
    while True:
        for sensor in active_sensors:
            try:
                response = requests.get(f"{SIMULATOR_URL}/api/sensors/{sensor}", timeout=5)
                if response.status_code == 200:
                    raw_data = response.json()
                    metrics = normalize_to_metrics(sensor, raw_data)
                    for metric in metrics:
                        topic = f"mars/metrics/{metric['sensor_id']}/{metric['metric_name']}"
                        mqtt_client.publish(topic, json.dumps(metric))
                        print(f"[POLL] {topic} -> {metric['value']} {metric['unit']}", flush=True)
            except Exception as e:
                print(f"Errore polling {sensor}: {e}", flush=True)
        time.sleep(5)

# --- THREAD 2: STREAMING TELEMETRIE (Nuova aggiunta SSE) ---


def get_telemetry_list():
    """Discovery dinamica delle telemetrie."""
    try:
        response = requests.get(f"{SIMULATOR_URL}/api/telemetry/topics", timeout=10)
        if response.status_code == 200:
            return response.json().get("topics", [])
    except Exception as e:
        print(f"Errore discovery telemetrie: {e}", flush=True)


def stream_telemetry(topic):

    stream_url = f"{SIMULATOR_URL}/api/telemetry/stream/{topic}" 
    
    print(f"Streaming TELEMETRIE (SSE) avviato su: {stream_url}", flush=True)
    
    while True:
        try:
            # stream=True mantiene la connessione aperta
            response = requests.get(stream_url, stream=True, timeout=None)
            client = sseclient.SSEClient(response)
            
            for event in client.events():
                if event.data:
                    raw_data = json.loads(event.data)
                    # Supponiamo che il simulatore invii l'ID nel campo 'id' o 'sensor_id'
                    item_id = raw_data.get("id") or raw_data.get("sensor_id", "telemetry_unknown")
                    
                    metrics = normalize_to_metrics(item_id, raw_data)
                    for metric in metrics:
                        # Usiamo un prefisso diverso (telemetry) per ordine nel broker
                        topic = f"mars/telemetry/{metric['sensor_id']}/{metric['metric_name']}"
                        mqtt_client.publish(topic, json.dumps(metric))
                        print(f"[STREAM] {topic} -> {metric['value']}", flush=True)
                        
        except Exception as e:
            print(f"Connessione SSE persa ({e}). Riconnessione in corso...", flush=True)
            time.sleep(5)

def cycle_telemetry():
    """Gestisce il flusso continuo di telemetrie tramite SSE."""
    # Endpoint standard per lo stream 
    topic_list = get_telemetry_list()

    for topic in topic_list:
        t_topic=threading.Thread(target=stream_telemetry, args=(topic,), daemon=True)
        t_topic.start()
    
# --- FASTAPI SETUP ---

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Connessione unica al Broker
    try:
        mqtt_client.connect(BROKER_HOST, BROKER_PORT, 60)
        mqtt_client.loop_start()
    except Exception as e:
        print(f"Impossibile connettersi al Broker: {e}", flush=True)

    # Avvio dei due thread in parallelo
    t_sensors = threading.Thread(target=poll_sensors, daemon=True)
    t_telemetry = threading.Thread(target=cycle_telemetry, daemon=True)
    
    t_sensors.start()
    t_telemetry.start()
    
    yield
    # Shutdown
    mqtt_client.loop_stop()
    mqtt_client.disconnect()

app = FastAPI(lifespan=lifespan)

@app.get("/health")
def health():
    return {
        "status": "ingestion alive", 
        "broker_connected": mqtt_client.is_connected()
    }
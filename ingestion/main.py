import requests
import time
import threading
import json
import paho.mqtt.client as mqtt
from fastapi import FastAPI
from contextlib import asynccontextmanager

# Configurazione
SIMULATOR_URL = "http://simulator:8080"
BROKER_HOST = "broker"
BROKER_PORT = 1883

# Inizializzazione Client MQTT
mqtt_client = mqtt.Client()
mqtt_client.username_pw_set("admin", "admin_password")

def normalize_to_metrics(sensor_id, raw_data):
    """
    Analizza il JSON e produce una lista di metriche piatte.
    Gestisce valori singoli, dizionari e liste di misure.
    """
    normalized_outputs = []
    timestamp = time.time()
    unit_generale = raw_data.get("unit", " ")

    # Funzione interna ricorsiva per estrarre i dati
    def extract(data, prefix=""):
        if isinstance(data, dict):
            for key, value in data.items():
                # Saltiamo i metadati che non sono misure
                if key in ["unit", "status", "timestamp", "sensor_id"]:
                    continue
                extract(value, f"{prefix}{key}" if not prefix else f"{prefix}_{key}")
        
        elif isinstance(data, list):
            for i, item in enumerate(data):
                extract(item, f"{prefix}_{i}")
        
        elif isinstance(data, (int, float)):
            # Abbiamo trovato un valore numerico! Creiamo la metrica
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
    """Interroga il simulatore per ottenere la lista dinamica dei sensori."""
    try:
        print(f"Tentativo di Discovery sensori presso {SIMULATOR_URL}/api/sensors...", flush=True)
        response = requests.get(f"{SIMULATOR_URL}/api/sensors", timeout=10)
        if response.status_code == 200:
            data = response.json()
            # Estraiamo la lista dalla chiave "sensors"
            sensors_list = data.get("sensors", [])
            
            if sensors_list:
                print(f"Discovery riuscita! Trovati {len(sensors_list)} sensori.", flush=True)
                return sensors_list
            else:
                print("ATTENZIONE: La chiave 'sensors' è vuota o mancante.", flush=True)
        else:
            print(f"Errore durante la discovery: Status {response.status_code}", flush=True)
    except Exception as e:
        print(f"Errore di connessione durante la discovery: {e}", flush=True)
    
    # Fallback in caso di errore (opzionale, per evitare che il thread crashi)
    return ["greenhouse_temperature", "hydroponic_ph", "water_tank_level"]

def poll_sensors():
    # 1. Connessione al Broker
    try:
        mqtt_client.connect(BROKER_HOST, BROKER_PORT, 60)
        mqtt_client.loop_start() 
    except Exception as e:
        print(f"Impossibile connettersi al Broker: {e}", flush=True)

    # 2. DISCOVERY DEI SENSORI (Eseguita una sola volta all'avvio)
    active_sensors = get_sensors_list()
    print(f"Discovery completata. Monitoraggio di {len(active_sensors)} sensori: {active_sensors}", flush=True)

    # 3. Ciclo di polling infinito
    while True:
        for sensor in active_sensors:
            try:
                response = requests.get(f"{SIMULATOR_URL}/api/sensors/{sensor}", timeout=5)
                if response.status_code == 200:
                    raw_data = response.json()
                    
                    # Generiamo la lista di metriche normalizzate
                    metrics = normalize_to_metrics(sensor, raw_data)
                    
                    # Inviamo ogni metrica come messaggio separato
                    for metric in metrics:
                        # Topic granulare: mars/metrics/sensor_name/metric_name
                        topic = f"mars/metrics/{metric['sensor_id']}/{metric['metric_name']}"
                        
                        mqtt_client.publish(topic, json.dumps(metric))
                        
                        # Log utile per l'hackathon
                        print(f"[PUB] {topic} -> {metric['value']} {metric['unit']}", flush=True)
                        print(metric)
                else:
                    print(f"Errore simulatore su {sensor}: {response.status_code}", flush=True)
            except Exception as e:
                print(f"Errore durante il processing di {sensor}: {e}", flush=True)
        
        time.sleep(5)

@asynccontextmanager
async def lifespan(app: FastAPI):
    thread = threading.Thread(target=poll_sensors, daemon=True)
    thread.start()
    yield
    mqtt_client.loop_stop()
    mqtt_client.disconnect()

app = FastAPI(lifespan=lifespan)

@app.get("/health")
def health():
    return {"status": "ingestion alive", "broker_connected": mqtt_client.is_connected()}
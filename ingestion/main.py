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
SENSORS = ["greenhouse_temperature", "hydroponic_ph", "water_tank_level"]

# Inizializzazione Client MQTT
mqtt_client = mqtt.Client()
mqtt_client.username_pw_set("admin", "admin_password")

def poll_sensors():
    print("Inizializzazione connessione al broker...", flush=True)
    try:
        mqtt_client.connect(BROKER_HOST, BROKER_PORT, 60)
        # Avviamo il loop del client MQTT in un thread separato per gestire riconnessioni automatiche
        mqtt_client.loop_start() 
    except Exception as e:
        print(f"Impossibile connettersi al Broker: {e}", flush=True)

    print("Background polling thread started...", flush=True)
    
    while True:
        for sensor in SENSORS:
            try:
                response = requests.get(f"{SIMULATOR_URL}/api/sensors/{sensor}", timeout=5)
                if response.status_code == 200:
                    raw_data = response.json()
                    
                    # 1. NORMALIZZAZIONE (Unified Event Schema)
                    payload = {
                        "sensor_id": sensor,
                        "value": raw_data.get("value"),
                        "unit": raw_data.get("unit"),
                        "timestamp": time.time(),
                        "status": "OK"
                    }
                    
                    # 2. PUBBLICAZIONE SUL BROKER
                    # Usiamo un topic strutturato: mars/sensors/<nome_sensore>
                    topic = f"mars/sensors/{sensor}"
                    mqtt_client.publish(topic, json.dumps(payload))
                    
                    print(f"Inviato a Broker -> {topic}: {payload['value']}", flush=True)
                else:
                    print(f"Errore simulatore su {sensor}: {response.status_code}", flush=True)
            
            except Exception as e:
                print(f"Errore durante il ciclo di polling: {e}", flush=True)
        
        time.sleep(5)

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Avvio del thread di polling
    thread = threading.Thread(target=poll_sensors, daemon=True)
    thread.start()
    yield
    # Cleanup allo spegnimento
    mqtt_client.loop_stop()
    mqtt_client.disconnect()

app = FastAPI(lifespan=lifespan)

@app.get("/health")
def health():
    return {"status": "ingestion alive", "broker_connected": mqtt_client.is_connected()}
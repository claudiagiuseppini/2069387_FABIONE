import requests
import time
import threading # Necessario per non bloccare il server
from fastapi import FastAPI
from contextlib import asynccontextmanager

SIMULATOR_URL = "http://simulator:8080"
SENSORS = ["greenhouse_temperature", "hydroponic_ph", "water_tank_level"]

def poll_sensors():
    print("Background thread started...")
    while True:
        for sensor in SENSORS:
            try:
                # Nota: qui usiamo l'URL del servizio 'simulator' [cite: 32]
                response = requests.get(f"{SIMULATOR_URL}/api/sensors/{sensor}")
                if response.status_code == 200:
                    data = response.json()
                    print(f"Dato Normalizzato: {sensor} -> {data.get('value')}", flush=True)
                else:
                    print(f"Errore su {sensor}: {response.status_code}", flush=True)
            except Exception as e:
                print(f"Errore di connessione a {SIMULATOR_URL}: {e}", flush=True)
        time.sleep(5)

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Avvia il polling in un thread separato
    thread = threading.Thread(target=poll_sensors, daemon=True)
    thread.start()
    yield

app = FastAPI(lifespan=lifespan)

@app.get("/health")
def health():
    return {"status": "ingestion alive"}
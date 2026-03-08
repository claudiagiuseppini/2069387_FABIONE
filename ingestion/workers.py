# workers.py
import time
import json
import requests
import sseclient
import threading
from config import SIMULATOR_URL, POLLING_INTERVAL
from normalization import normalize_data
from broker import conn_poll, conn_telemetry, connect_stomp
from simulator_client import get_sensors_list, get_telemetry_list

def poll_sensors_worker():
    active_sensors = get_sensors_list()
    print(f"🚀 Polling SENSORI avviato su: {active_sensors}", flush=True)
    
    while True:
        connect_stomp(conn_poll, "POLLING")
        for sensor in active_sensors:
            try:
                r = requests.get(f"{SIMULATOR_URL}/api/sensors/{sensor}", timeout=5)
                if r.status_code == 200:
                    schema = normalize_data(r.json())
                    topic = f"/topic/mars.metrics.{schema['sensor_id']}"
                    
                    # Invio al Broker
                    conn_poll.send(body=json.dumps(schema), destination=topic)
                    
                    # LOG REINSERITI
                    for metric in schema['metrics']:
                        print(f"[POLL] {topic} -> {metric['name']} {metric['value']} {metric['unit']}", flush=True)
                else:
                    print(f"❌ Errore simulatore su {sensor}: {r.status_code}", flush=True)
            except Exception as e:
                print(f"❌ Errore durante il processing di {sensor}: {e}", flush=True)
        
        time.sleep(POLLING_INTERVAL)

def stream_telemetry_worker(topic_id):
    url = f"{SIMULATOR_URL}/api/telemetry/stream/{topic_id}"
    print(f"Streaming TELEMETRIE (SSE) avviato su: {url}", flush=True)
    
    while True:
        try:
            connect_stomp(conn_telemetry, "TELEMETRY")
            response = requests.get(url, stream=True, timeout=None)
            client = sseclient.SSEClient(response)
            
            for event in client.events():
                if event.data:
                    raw_data = json.loads(event.data)
                    schema = normalize_data(raw_data)
                    dest_topic = f"/topic/mars.telemetry.{schema['sensor_id']}"
                    
                    # Invio al Broker
                    conn_telemetry.send(body=json.dumps(schema), destination=dest_topic)
                    
                    # LOG REINSERITI
                    for metric in schema['metrics']:
                        print(f"[STREAM] {dest_topic} -> {metric['name']} {metric['value']} {metric['unit'] or ''}", flush=True)
        except Exception as e:
            print(f"⚠️ Connessione SSE persa ({e}). Riconnessione in 5s...", flush=True)
            time.sleep(5)

def start_workers():
    # Avvio polling sensori in un thread
    threading.Thread(target=poll_sensors_worker, daemon=True).start()
    
    # Avvio uno stream SSE per ogni topic di telemetria
    topic_list = get_telemetry_list()
    for topic in topic_list:
        threading.Thread(target=stream_telemetry_worker, args=(topic,), daemon=True).start()
        time.sleep(2.0) # Delay per non sovraccaricare il broker al boot
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
    '''Interrogates sensors, normalizes data and publish them on broker'''

    active_sensors = get_sensors_list()
    print(f"SENSORS polling started on: {active_sensors}", flush=True)
    
    while True:
        # open stomp connection
        connect_stomp(conn_poll, "POLLING")

        # poll metrics from every sensor
        for sensor in active_sensors:
            try:
                # send request to sensor
                r = requests.get(f"{SIMULATOR_URL}/api/sensors/{sensor}", timeout=5)
                if r.status_code == 200:
                    schema = normalize_data(r.json())
                    topic = f"/topic/mars.metrics.{schema['sensor_id']}"
                    
                    # Send sensor normalized data to broker
                    conn_poll.send(body=json.dumps(schema), destination=topic)
                    
                    # Restored logs
                    for metric in schema['metrics']:
                        print(f"[POLL] {topic} -> {metric['name']} {metric['value']} {metric['unit']}", flush=True)
                else:
                    print(f"❌ Simulator error on {sensor}: {r.status_code}", flush=True)
            except Exception as e:
                print(f"❌ Error during processing on {sensor}: {e}", flush=True)
        
        time.sleep(POLLING_INTERVAL)

def stream_telemetry_worker(topic_id):
    '''Receives messages from telemetries, normalizes data and publish them on broker'''

    # defines simulation endpoint for SSE streaming
    url = f"{SIMULATOR_URL}/api/telemetry/stream/{topic_id}"
    print(f"TELEMETRIES Streaming (SSE) started on: {url}", flush=True)
    
    while True:
        try:
            # open stomp connection
            connect_stomp(conn_telemetry, "TELEMETRY")

            # set up HTTP GET request with stream=True and SSE client to mantain the connection open
            response = requests.get(url, stream=True, timeout=None)
            client = sseclient.SSEClient(response)
            
            for event in client.events():
                if event.data:
                    raw_data = json.loads(event.data)

                    # normalized received data and defines broker destination
                    schema = normalize_data(raw_data)
                    dest_topic = f"/topic/mars.telemetry.{schema['sensor_id']}"
                    
                    # Send normalized data to broker
                    conn_telemetry.send(body=json.dumps(schema), destination=dest_topic)
                    
                    # Restored logs
                    for metric in schema['metrics']:
                        print(f"[STREAM] {dest_topic} -> {metric['name']} {metric['value']} {metric['unit'] or ''}", flush=True)
        except Exception as e:
            print(f"⚠️ SSE Connection lost ({e}). Riconnecting in 5s...", flush=True)
            time.sleep(5)

def start_workers():
    # Start sensor polling in a thread
    threading.Thread(target=poll_sensors_worker, daemon=True).start()
    
    # Start one SSE stream for each telemetry topic
    topic_list = get_telemetry_list()
    for topic in topic_list:
        threading.Thread(target=stream_telemetry_worker, args=(topic,), daemon=True).start()
        time.sleep(2.0) # Delay to avoid overloading the broker at boot
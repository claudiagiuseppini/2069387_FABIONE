# broker.py
import stomp
from config import BROKER_HOST, BROKER_PORT, BROKER_USER, BROKER_PASS

conn_poll = stomp.Connection([(BROKER_HOST, BROKER_PORT)])
conn_telemetry = stomp.Connection([(BROKER_HOST, BROKER_PORT)])

def connect_stomp(conn, label):
    try:
        if not conn.is_connected():
            conn.connect(BROKER_USER, BROKER_PASS, wait=True)
            print(f"✅ Connesso al Broker ({label})", flush=True)
    except Exception as e:
        print(f"❌ Errore STOMP ({label}): {e}", flush=True)
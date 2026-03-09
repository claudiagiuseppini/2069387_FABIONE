# broker.py
import stomp
from config import BROKER_HOST, BROKER_PORT, BROKER_USER, BROKER_PASS

# define stomp connections
conn_poll = stomp.Connection([(BROKER_HOST, BROKER_PORT)])
conn_telemetry = stomp.Connection([(BROKER_HOST, BROKER_PORT)])

def connect_stomp(conn, label):
    '''This function attempts to connect to the broker using the credentials 
    defined in the system configuration.'''
    try:
        if not conn.is_connected():
            conn.connect(BROKER_USER, BROKER_PASS, wait=True)
            print(f"✅ Connected to Broker ({label})", flush=True)
    except Exception as e:
        print(f"❌ STOMP Error({label}): {e}", flush=True)
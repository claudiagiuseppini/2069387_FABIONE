import time
import stomp
from config import BROKER_CONF
from engine import process_message

# required class for stomp connection
class StompBridge(stomp.ConnectionListener):
    def on_message(self, frame):
        # on message reception event, call message processing
        process_message(frame.body, frame.headers.get("destination", "unknown"))
    def on_error(self, frame):
        print(f"❌ Error on STOMP: {frame.body}", flush=True)
    def on_disconnected(self):
        print("Lost STOMP Connection.", flush=True)

def run_service():
    '''Initializes services and keeps it active'''

    print("Processing Service Activation...", flush=True)

    # sets up broker connection
    conn = stomp.Connection([(BROKER_CONF["host"], BROKER_CONF["port"])])
    conn.set_listener("", StompBridge())

    # checks if connection is up. If it's not, tries connecting again
    while True:
        try:
            if not conn.is_connected():
                conn.connect(BROKER_CONF["user"], BROKER_CONF["pass"], wait=True)
                conn.subscribe(destination="/topic/mars.#", id="processing_sub", ack="auto")
                print("✅ Connected to Broker and subscribed to '/topic/mars.#'", flush=True)
            time.sleep(10)
        except Exception as e:
            print(f"Failed reconnection: {e}", flush=True)
            time.sleep(5)

if __name__ == "__main__":
    run_service()
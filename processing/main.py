import time
import stomp
from config import BROKER_CONF
from engine import process_message

class StompBridge(stomp.ConnectionListener):
    def on_message(self, frame):
        process_message(frame.body, frame.headers.get("destination", "unknown"))
    def on_error(self, frame):
        print(f"❌ Errore STOMP: {frame.body}", flush=True)
    def on_disconnected(self):
        print("🔄 Connessione STOMP persa.", flush=True)

def run_service():
    print("🚀 Avvio Processing Service...", flush=True)
    conn = stomp.Connection([(BROKER_CONF["host"], BROKER_CONF["port"])])
    conn.set_listener("", StompBridge())

    while True:
        try:
            if not conn.is_connected():
                conn.connect(BROKER_CONF["user"], BROKER_CONF["pass"], wait=True)
                conn.subscribe(destination="/topic/mars.#", id="processing_sub", ack="auto")
                print("✅ Connesso al Broker e sottoscritto a '/topic/mars.#'", flush=True)
            time.sleep(10)
        except Exception as e:
            print(f"🔄 Tentativo di riconnessione fallito: {e}", flush=True)
            time.sleep(5)

if __name__ == "__main__":
    run_service()
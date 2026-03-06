import stomp
import json
import time
import sys

# Configurazione
BROKER_HOST = "broker"
BROKER_PORT = 61613  # Porta STOMP
BROKER_USER = "admin"
BROKER_PASS = "admin_password"

class ProcessingListener(stomp.ConnectionListener):
    """Classe per gestire gli eventi e i messaggi in arrivo dal broker."""
    
    def on_error(self, frame):
        print(f"❌ Errore STOMP ricevuto: {frame.body}", flush=True)

    def on_message(self, frame):
        # frame.headers contiene i metadati (es. destination)
        # frame.body contiene il payload JSON
        topic = frame.headers.get('destination')
        print(f"🔔 Notifica: Ricevuto messaggio su {topic}", flush=True)
        
        try:
            data = json.loads(frame.body)
            # Estraiamo i dati usando la stessa logica del tuo codice precedente
            sensor_id = data.get('sensor_id', 'unknown')
            metric_name = data.get('metric_name', 'unknown')
            value = data.get('value')
            unit = data.get('unit', '')
            
            print(f"   📊 SENSOR: {sensor_id} | METRIC: {metric_name} | VAL: {value} {unit}", flush=True)
        except Exception as e:
            print(f"⚠️ Errore decodifica: {e} | Raw: {frame.body}", flush=True)

    def on_disconnected(self):
        print("🔄 Connessione STOMP persa. Tentativo di riconnessione...", flush=True)

# Inizializzazione Client STOMP
conn = stomp.Connection([(BROKER_HOST, BROKER_PORT)])
conn.set_listener('', ProcessingListener())

def start_processing():
    print("🚀 Avvio Processing Service (STOMP Mode)...", flush=True)
    
    while True:
        try:
            if not conn.is_connected():
                conn.connect(BROKER_USER, BROKER_PASS, wait=True)
                
                # Sottoscrizione: 
                # In Artemis STOMP, il wildcard '>' equivale al '#' di MQTT.
                # Ascoltiamo tutto il ramo /topic/mars.
                conn.subscribe(destination='/topic/mars.#', id='processing_sub', ack='auto')
                print("✅ Connesso e sottoscritto a /topic/mars/>", flush=True)
            
            # Manteniamo il thread principale vivo
            time.sleep(10)
            
        except Exception as e:
            print(f"❌ Errore durante la connessione: {e}", flush=True)
            time.sleep(5)

if __name__ == "__main__":
    start_processing()
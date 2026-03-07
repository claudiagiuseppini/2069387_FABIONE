import stomp
import json
import time
import operator
import mysql.connector
from dataclasses import dataclass
from typing import Optional

# variabili statiche
OPERATORS = {
    '>': operator.gt,
    '<': operator.lt,
    '>=': operator.ge,
    '<=': operator.le,
    '=': operator.eq
}

# --- CONFIGURAZIONE ---
BROKER_CONF = {"host": "broker", "port": 61613, "user": "admin", "pass": "admin_password"}
DB_CONF = {
    "host": "db",
    "user": "user_mars",
    "password": "password_mars",
    "database": "mars_iot"
}

# --- STRUTTURA DATI (La nostra "piccola parentesi") ---
@dataclass
class Metric:
    sensor_id: str
    sensor_type: str        
    metric_name: str
    value: float
    unit: Optional[str]
    timestamp: str          
    source: Optional[str]   
    status: str

# --- LOGICA DATABASE ---
def get_db_connection():
    """Crea una nuova connessione al database MariaDB."""
    try:
        return mysql.connector.connect(**DB_CONF)
    except Exception as e:
        print(f"❌ Errore connessione DB: {e}", flush=True)
        return None

def get_rules(metric: Metric):
    """Recupera le regole dal DB per la metrica specifica."""
    conn = get_db_connection()
    rules = []
    if not conn: return rules
    
    try:
        cursor = conn.cursor(dictionary=True) # dictionary=True rende l'accesso più facile
        query = """
            SELECT operator, threshold, actuator_name, action_value 
            FROM automation_rules 
            WHERE sensor_name = %s AND metric_name = %s AND enabled = TRUE
            LIMIT 1
        """
        cursor.execute(query, (metric.sensor_id, metric.metric_name))
        rules = cursor.fetchall()
        cursor.close()
    except Exception as e:
        print(f"⚠️ Errore lettura regole SQL: {e}", flush=True)
    finally:
        conn.close()
    if rules:
        return rules[0]
    else:
        return None

# --- LOGICA APPLICATIVA (Regole e Attuatori) ---
def check_rules_and_actuate(metric: Metric):
    """Analizza il dato rispetto alle regole salvate nel DB."""
    # 1. Recupera le regole per questo sensore/metrica
    rule = get_rules(metric)
    if rule:
        op_str = rule['operator']  # es: '>'
        threshold = rule['threshold']
        
        # 2. Trasforma la stringa in operazione logica
        op_func = OPERATORS.get(op_str)
        
        if op_func and op_func(metric.value, threshold):
            # 3. Se la regola è soddisfatta, esegui l'azione
            print(f"🎯 REGOLA ATTIVATA: {metric.sensor_id} {op_str} {threshold}", flush=True)
            send_actuator_command(
                actuator_id=rule['actuator_name'], 
                command=rule['action_value']
            )
    else:
        print("Nessuna regola attiva")

def send_actuator_command(actuator_id: str, command: str):
    """Invia un comando al simulatore."""

    #TODO

# --- PIPELINE DI ELABORAZIONE ---
def process_message(body: str, topic: str):
    """Funzione principale che trasforma il nuovo schema unificato in azione."""
    try:
        data = json.loads(body)
        
        # Estraiamo l'oggetto interno delle metriche per comodità
        inner_metric = data.get('metric', {})
        
        # Mappiamo il JSON sulla Dataclass
        m = Metric(
            sensor_id=data.get('sensor_id', 'unknown'),
            sensor_type=data.get('sensor_type', 'unknown'),
            metric_name=inner_metric.get('name', 'unknown'),  
            value=float(inner_metric.get('value', 0.0)),      
            unit=inner_metric.get('unit', ''),               
            timestamp=data.get('timestamp', ''),
            source=data.get('source'),
            status=data.get('status', 'ok')
        )
        
        print(f"🔔 Notifica [{m.sensor_type}]: {m.sensor_id}.{m.metric_name} = {m.value} {m.unit}", flush=True)
        
        # Eseguiamo le regole (passando l'oggetto Metric aggiornato)
        check_rules_and_actuate(m)
        
    except json.JSONDecodeError:
        print(f"⚠️ Messaggio non JSON: {body[:50]}...", flush=True)
    except Exception as e:
        print(f"⚠️ Errore processamento su topic {topic}: {e}", flush=True)

# --- INFRASTRUTTURA STOMP ---
class StompBridge(stomp.ConnectionListener):
    """Ponte minimo tra il protocollo STOMP e le nostre funzioni."""
    def on_message(self, frame):
        process_message(frame.body, frame.headers.get('destination'))
    
    def on_error(self, frame):
        print(f"❌ Errore STOMP: {frame.body}", flush=True)
    
    def on_disconnected(self):
        print("🔄 Connessione STOMP persa.", flush=True)

# --- CICLO PRINCIPALE ---
def run_service():
    print("🚀 Avvio Processing Service Funzionale...", flush=True)
    
    # Inizializziamo la connessione
    conn = stomp.Connection([(BROKER_CONF["host"], BROKER_CONF["port"])])
    conn.set_listener('', StompBridge())
    
    while True:
        try:
            if not conn.is_connected():
                conn.connect(BROKER_CONF["user"], BROKER_CONF["pass"], wait=True)
                # Sottoscrizione con wildcard per Artemis
                conn.subscribe(destination='/topic/mars.#', id='processing_sub', ack='auto')
                print("✅ Connesso al Broker e sottoscritto a '/topic/mars.#'", flush=True)
            
            time.sleep(10) # Mantiene il thread vivo
        except Exception as e:
            print(f"🔄 Tentativo di riconnessione... {e}", flush=True)
            time.sleep(5)

if __name__ == "__main__":
    run_service()
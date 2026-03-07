import stomp
import json
import time
import operator
import requests
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
BROKER_CONF = {
    "host": "broker",
    "port": 61613,
    "user": "admin",
    "pass": "admin_password"
}

DB_CONF = {
    "host": "db",
    "user": "user_mars",
    "password": "password_mars",
    "database": "mars_iot"
}

SIMULATOR_URL = "http://simulator:8080"

# --- STRUTTURA DATI ---
@dataclass
class Metric:
    sensor_id: str
    sensor_type: str        
    values: dict            # Esempio: {'temperature_c': 24.8, 'humidity_pct': 45}
    units: dict             # Esempio: {'temperature_c': 'C', 'humidity_pct': '%'}
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
    """Recupera tutte le regole attive dal DB per la metrica specifica."""
    conn = get_db_connection()
    rules = []

    if not conn:
        return rules

    try:
        cursor = conn.cursor(dictionary=True)
        query = """
            SELECT id, metric_name, operator, threshold, actuator_name, action_value
            FROM automation_rules
            WHERE sensor_name = %s AND enabled = TRUE
        """
        cursor.execute(query, (metric.sensor_id,))
        rules = cursor.fetchall()
        cursor.close()
    except Exception as e:
        print(f"⚠️ Errore lettura regole SQL: {e}", flush=True)
    finally:
        conn.close()

    return rules


# --- LOGICA APPLICATIVA (Regole e Attuatori) ---
from collections import Counter

def check_rules_and_actuate(metric: Metric):
    """
    Analizza le metriche con supporto all'astensione (zona morta).
    L'attuatore viene comandato solo se c'è almeno un voto attivo.
    """
    rules = get_rules(metric)
    if not rules:
        return

    votes = []
    
    for rule in rules:
        m_name = rule["metric_name"]
        if m_name not in metric.values:
            continue

        val = metric.values[m_name]
        op_func = OPERATORS.get(rule["operator"])
        threshold = rule["threshold"]
        action = rule["action_value"]

        try:
            # Una metrica vota SOLO se la sua condizione è vera
            if op_func(val, threshold):
                votes.append(action)
        except Exception as e:
            print(f"⚠️ Errore valutazione regola {rule.get('id')}: {e}", flush=True)

    # --- Logica di Decisione ---
    
    if not votes:
        # CASO ASTENSIONE TOTALE: 
        # Nessuna metrica è sopra la soglia ON o sotto la soglia OFF.
        # Non inviamo alcun comando per lasciare l'attuatore nello stato in cui si trova.
        return

    # Se ci sono voti, applichiamo la maggioranza
    counts = Counter(votes)
    final_decision, _ = counts.most_common(1)[0]
    
    print(f"⚖️  DECISIONE: {dict(counts)} -> Vince {final_decision}", flush=True)

    target_actuator = rules[0]["actuator_name"]
    send_actuator_command(target_actuator, final_decision)


def send_actuator_command(actuator_id: str, command: str):
    """Invia un comando al simulatore via REST."""
    try:
        response = requests.post(
            f"{SIMULATOR_URL}/api/actuators/{actuator_id}",
            json={"state": command},
            timeout=5
        )

        if response.status_code in (200, 201):
            print(f"⚙️ Comando inviato con successo: {actuator_id} -> {command}", flush=True)
        else:
            print(
                f"❌ Errore comando attuatore {actuator_id}: "
                f"status={response.status_code}, body={response.text}",
                flush=True
            )
    except Exception as e:
        print(f"❌ Errore richiesta REST verso attuatore {actuator_id}: {e}", flush=True)


# --- PIPELINE DI ELABORAZIONE ---
def process_message(body: str, topic: str):
    """Trasforma il messaggio JSON con lista di metriche in un unico oggetto Metric."""
    try:
        data = json.loads(body)
        
        # 1. Recuperiamo la lista 'metrics' dalJSON normalizzato
        raw_metrics = data.get("metrics", [])

        # 2. Creiamo dizionari per mappare i nomi ai valori/unità
        # Questo ci permette di fare m.values['temperature_c'] nelle regole
        metrics_values = {m['name']: m['value'] for m in raw_metrics}
        metrics_units = {m['name']: m['unit'] for m in raw_metrics}

        # 3. Creiamo un unico oggetto Metric che contiene tutto il pacchetto
        m = Metric(
            sensor_id=data.get("sensor_id", "unknown"),
            sensor_type=data.get("sensor_type", "unknown"),
            values=metrics_values,  # <--- Dizionario di valori
            units=metrics_units,    # <--- Dizionario di unità
            timestamp=data.get("timestamp", ""),
            source=data.get("source"),
            status=data.get("status", "ok")
        )

        # 4. Print di log per mostrare tutte le metriche insieme
        metrics_str = ", ".join([f"{k}={v}{metrics_units.get(k, '')}" for k, v in metrics_values.items()])
        print(
            f"🔔 Notifica [{m.sensor_type}] da {m.sensor_id}: {metrics_str}",
            flush=True
        )

        # 5. Chiamiamo check_rules passandogli l'intero pacchetto
        check_rules_and_actuate(m)

    except json.JSONDecodeError:
        print(f"⚠️ Messaggio non JSON su topic {topic}: {body[:100]}...", flush=True)
    except Exception as e:
        print(f"⚠️ Errore processamento su topic {topic}: {e}", flush=True)


# --- INFRASTRUTTURA STOMP ---
class StompBridge(stomp.ConnectionListener):
    """Bridge tra STOMP e la logica applicativa."""

    def on_message(self, frame):
        process_message(frame.body, frame.headers.get("destination", "unknown"))

    def on_error(self, frame):
        print(f"❌ Errore STOMP: {frame.body}", flush=True)

    def on_disconnected(self):
        print("🔄 Connessione STOMP persa.", flush=True)


# --- CICLO PRINCIPALE ---
def run_service():
    print("🚀 Avvio Processing Service...", flush=True)

    conn = stomp.Connection([(BROKER_CONF["host"], BROKER_CONF["port"])])
    conn.set_listener("", StompBridge())

    while True:
        try:
            if not conn.is_connected():
                conn.connect(
                    BROKER_CONF["user"],
                    BROKER_CONF["pass"],
                    wait=True
                )
                conn.subscribe(
                    destination="/topic/mars.#",
                    id="processing_sub",
                    ack="auto"
                )
                print("✅ Connesso al Broker e sottoscritto a '/topic/mars.#'", flush=True)

            time.sleep(10)

        except Exception as e:
            print(f"🔄 Tentativo di riconnessione fallito: {e}", flush=True)
            time.sleep(5)


if __name__ == "__main__":
    run_service()
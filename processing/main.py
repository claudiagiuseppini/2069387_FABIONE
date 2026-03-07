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
    """Recupera tutte le regole attive dal DB per la metrica specifica."""
    conn = get_db_connection()
    rules = []

    if not conn:
        return rules

    try:
        cursor = conn.cursor(dictionary=True)
        query = """
            SELECT id, operator, threshold, actuator_name, action_value
            FROM automation_rules
            WHERE sensor_name = %s
              AND metric_name = %s
              AND enabled = TRUE
        """
        cursor.execute(query, (metric.sensor_id, metric.metric_name))
        rules = cursor.fetchall()
        cursor.close()
    except Exception as e:
        print(f"⚠️ Errore lettura regole SQL: {e}", flush=True)
    finally:
        conn.close()

    return rules


# --- LOGICA APPLICATIVA (Regole e Attuatori) ---
def check_rules_and_actuate(metric: Metric):
    """Analizza il dato rispetto alle regole salvate nel DB."""
    rules = get_rules(metric)

    if not rules:
        print(f"ℹ️ Nessuna regola attiva per {metric.sensor_id}.{metric.metric_name}", flush=True)
        return

    for rule in rules:
        op_str = rule["operator"]
        threshold = rule["threshold"]
        op_func = OPERATORS.get(op_str)

        if not op_func:
            print(f"⚠️ Operatore non supportato nella regola {rule.get('id')}: {op_str}", flush=True)
            continue

        try:
            if op_func(metric.value, threshold):
                print(
                    f"🎯 REGOLA ATTIVATA [rule_id={rule.get('id')}]: "
                    f"{metric.sensor_id}.{metric.metric_name} {op_str} {threshold}",
                    flush=True
                )

                send_actuator_command(
                    actuator_id=rule["actuator_name"],
                    command=rule["action_value"]
                )
            else:
                print(
                    f"➖ Regola non attivata [rule_id={rule.get('id')}]: "
                    f"{metric.value} {op_str} {threshold} -> False",
                    flush=True
                )
        except Exception as e:
            print(f"⚠️ Errore valutazione regola {rule.get('id')}: {e}", flush=True)


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
    """Trasforma il messaggio JSON normalizzato in una metrica processabile."""
    try:
        data = json.loads(body)

        inner_metric = data.get("metric", {})

        m = Metric(
            sensor_id=data.get("sensor_id", "unknown"),
            sensor_type=data.get("sensor_type", "unknown"),
            metric_name=inner_metric.get("name", "unknown"),
            value=float(inner_metric.get("value", 0.0)),
            unit=inner_metric.get("unit", ""),
            timestamp=data.get("timestamp", ""),
            source=data.get("source"),
            status=data.get("status", "ok")
        )

        print(
            f"🔔 Notifica [{m.sensor_type}] da topic={topic}: "
            f"{m.sensor_id}.{m.metric_name} = {m.value} {m.unit or ''}",
            flush=True
        )

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
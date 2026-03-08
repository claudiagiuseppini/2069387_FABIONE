import json
from collections import Counter
from config import OPERATORS
from models import Metric
from database import get_rules_from_db
from simulator_client import send_actuator_command

def process_message(body: str, topic: str):
    try:
        data = json.loads(body)
        raw_metrics = data.get("metrics", [])
        
        m = Metric(
            sensor_id=data.get("sensor_id", "unknown"),
            sensor_type=data.get("sensor_type", "unknown"),
            values={met['name']: met['value'] for met in raw_metrics},
            units={met['name']: met['unit'] for met in raw_metrics},
            timestamp=data.get("timestamp", ""),
            source=data.get("source"),
            status=data.get("status", "ok")
        )

        metrics_str = ", ".join([f"{k}={v}{m.units.get(k, '')}" for k, v in m.values.items()])
        print(f"🔔 Notifica [{m.sensor_type}] da {m.sensor_id}: {metrics_str}", flush=True)

        evaluate_logic(m)

    except Exception as e:
        print(f"⚠️ Errore processamento su topic {topic}: {e}", flush=True)

def evaluate_logic(metric: Metric):
    rules = get_rules_from_db(metric.sensor_id)
    if not rules: return

    votes = []
    for rule in rules:
        m_name = rule["metric_name"]
        if m_name in metric.values:
            val = metric.values[m_name]
            op_func = OPERATORS.get(rule["operator"])
            if op_func(val, rule["threshold"]):
                votes.append(rule["action_value"])

    if votes:
        counts = Counter(votes)
        final_decision, _ = counts.most_common(1)[0]
        print(f"⚖️  DECISIONE: {dict(counts)} -> Vince {final_decision}", flush=True)
        send_actuator_command(rules[0]["actuator_name"], final_decision)
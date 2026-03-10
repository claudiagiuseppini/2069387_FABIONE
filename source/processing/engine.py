import json
from collections import Counter
from config import OPERATORS
from models import Metric
from database import get_rules_from_db
from simulator_client import send_actuator_command

def process_message(body: str, topic: str):
    '''receive, read and prepare the message in the normalized schema'''
    try:
        # receive normalized message
        data = json.loads(body)
        raw_metrics = data.get("metrics", [])
        
        # initialize variable to store the received message
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
        print(f"🔔 Notification [{m.sensor_type}] from {m.sensor_id}: {metrics_str}", flush=True)

        # make a decision based  on the data
        evaluate_logic(m)

    except Exception as e:
        print(f"⚠️ Error processing ontopic {topic}: {e}", flush=True)

def evaluate_logic(metric: Metric):
    '''Get rules from the database, make a decision based on the rule, and calls the function to take action 
    on the actuators in the simulator'''

    # call function to get db rules
    rules = get_rules_from_db(metric.sensor_id)
    if not rules: return

    # majority voting between metrics from the same sensor to make a decision over actuators
    votes = []
    for rule in rules:
        m_name = rule["metric_name"]
        if m_name in metric.values:
            val = metric.values[m_name]
            op_func = OPERATORS.get(rule["operator"])
            if op_func(val, rule["threshold"]):
                votes.append(rule["action_value"])

    # based on votes, calls function to activate/deactivate actuators 
    if votes:
        counts = Counter(votes)
        final_decision, _ = counts.most_common(1)[0]
        print(f"DECISION: {dict(counts)} -> {final_decision}", flush=True)
        send_actuator_command(rules[0]["actuator_name"], final_decision)
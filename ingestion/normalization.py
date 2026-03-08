# normalization.py
def normalize_data(raw_data: dict):
    # Logica sensor_id / sensor_type
    if "sensor_id" in raw_data:
        sensor_id = raw_data["sensor_id"]
        sensor_type = "sensor"
    elif "topic" in raw_data:
        sensor_id = raw_data["topic"].replace("/topic/mars/", "").replace("mars/telemetry/", "")
        sensor_type = "telemetric"
    else:
        sensor_id = "unknown"
        sensor_type = "unknown"

    timestamp = raw_data.get("captured_at") or raw_data.get("event_time")
    status = raw_data.get("status") or raw_data.get("last_state", "ok")

    # Logica Source
    source = None
    if "subsystem" in raw_data: source = raw_data["subsystem"]
    elif isinstance(raw_data.get("source"), dict): source = raw_data["source"].get("segment")
    elif "loop" in raw_data: source = raw_data["loop"]
    elif "airlock_id" in raw_data: source = raw_data["airlock_id"]

    metrics_to_process = []
    if "measurements" in raw_data and isinstance(raw_data["measurements"], list):
        for m in raw_data["measurements"]:
            metrics_to_process.append((m.get("metric"), m.get("value"), m.get("unit")))
    elif "metric" in raw_data and "value" in raw_data:
        metrics_to_process.append((raw_data.get("metric"), raw_data.get("value"), raw_data.get("unit")))
    else:
        potential_metrics = [
            "pm1_ug_m3", "pm25_ug_m3", "pm10_ug_m3", "level_pct", "level_liters",
            "power_kw", "voltage_v", "current_a", "cumulative_kwh",
            "temperature_c", "flow_l_min", "cycles_per_hour"
        ]
        for key in potential_metrics:
            if key in raw_data:
                metrics_to_process.append((key, raw_data[key], None))

    metric_list = [{"name": str(n), "value": v, "unit": u or ""} for n, v, u in metrics_to_process]

    normalized_schema = {
        "sensor_id": sensor_id,
        "sensor_type": sensor_type,
        "timestamp": timestamp,
        "source": source,
        "status": status,
        "metrics": metric_list
    }

    print(normalized_schema)
    return normalized_schema
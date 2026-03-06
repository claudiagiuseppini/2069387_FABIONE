
CREATE TABLE IF NOT EXISTS automation_rules (
    id INT AUTO_INCREMENT PRIMARY KEY,
    sensor_name VARCHAR(255) NOT NULL, -- es. greenhouse_temperature
    metric_name VARCHAR(255) NOT NULL,
    operator VARCHAR(2) NOT NULL,      -- <, <=, =, >, >= [cite: 97]
    threshold FLOAT NOT NULL,          -- Valore di soglia
    actuator_name VARCHAR(255) NOT NULL, -- es. cooling_fan
    action_value VARCHAR(10) NOT NULL, -- ON / OFF
    enabled BOOLEAN DEFAULT TRUE
);

-- Inserimento di alcune regole di base (Esempi richiesti dalla consegna [cite: 98])
INSERT INTO automation_rules (sensor_name, operator, threshold, actuator_name, action_value) 
VALUES ('greenhouse_temperature', 'temperature_c', '>', 24.7, 'cooling_fan', 'ON');

INSERT INTO automation_rules (sensor_name, operator, threshold, actuator_name, action_value) 
VALUES ('entrance_humidity', 'humidity_pct', '<', 30.0, 'entrance_humidifier', 'ON');

INSERT INTO automation_rules (sensor_name, operator, threshold, actuator_name, action_value) 
VALUES ('co2_hall', 'co2_ppm', '>', 1000.0, 'hall_ventilation', 'ON');

CREATE TABLE IF NOT EXISTS automation_rules (
    id INT AUTO_INCREMENT PRIMARY KEY,
    sensor_name VARCHAR(255) NOT NULL, -- es. greenhouse_temperature
    metric_name VARCHAR(255) NOT NULL,
    metric_name, operator VARCHAR(2) NOT NULL,      -- <, <=, =, >, >= [cite: 97]
    threshold FLOAT NOT NULL,          -- Valore di soglia
    actuator_name VARCHAR(255) NOT NULL, -- es. cooling_fan
    action_value VARCHAR(10) NOT NULL, -- ON / OFF
    enabled BOOLEAN DEFAULT TRUE
);

-- Inserimento di alcune regole di base (Esempi richiesti dalla consegna [cite: 98])
INSERT INTO automation_rules (sensor_name, metric_name, operator, threshold, actuator_name, action_value) 
VALUES ('greenhouse_temperature', 'temperature_c', '>', 27, 'cooling_fan', 'ON');

INSERT INTO automation_rules (sensor_name, metric_name, operator, threshold, actuator_name, action_value) 
VALUES ('greenhouse_temperature', 'temperature_c', '<', 23, 'cooling_fan', 'OFF');

INSERT INTO automation_rules (sensor_name, metric_name, operator, threshold, actuator_name, action_value) 
VALUES ('entrance_humidity', 'humidity_pct', '<', 28, 'entrance_humidifier', 'ON');

INSERT INTO automation_rules (sensor_name, metric_name, operator, threshold, actuator_name, action_value) 
VALUES ('entrance_humidity', 'humidity_pct', '>', 31, 'entrance_humidifier', 'OFF');

INSERT INTO automation_rules (sensor_name, metric_name, operator, threshold, actuator_name, action_value) 
VALUES ('co2_hall', 'co2_ppm', '>', 1300.0, 'hall_ventilation', 'ON');

INSERT INTO automation_rules (sensor_name, metric_name, operator, threshold, actuator_name, action_value) 
VALUES ('co2_hall', 'co2_ppm', '<', 1280.0, 'hall_ventilation', 'OFF');

INSERT INTO automation_rules (sensor_name, metric_name, operator, threshold, actuator_name, action_value) 
VALUES ('corridor_pressure', 'pressure_kpa', '<', 100, 'hall_ventilation', 'ON');

INSERT INTO automation_rules (sensor_name, metric_name, operator, threshold, actuator_name, action_value) 
VALUES ('corridor_pressure', 'pressure_kpa', '>', 101, 'hall_ventilation', 'OFF');

INSERT INTO automation_rules (sensor_name, metric_name, operator, threshold, actuator_name, action_value) 
VALUES ('air_quality_pm25', 'pm1_ug_m3', '>', 15, 'hall_ventilation', 'ON');

INSERT INTO automation_rules (sensor_name, metric_name, operator, threshold, actuator_name, action_value) 
VALUES ('air_quality_pm25', 'pm1_ug_m3', '<', 12, 'hall_ventilation', 'OFF');

INSERT INTO automation_rules (sensor_name, metric_name, operator, threshold, actuator_name, action_value) 
VALUES ('air_quality_pm25', 'pm25_ug_m3', '>', 18, 'hall_ventilation', 'ON');

INSERT INTO automation_rules (sensor_name, metric_name, operator, threshold, actuator_name, action_value) 
VALUES ('air_quality_pm25', 'pm25_ug_m3', '<', 15, 'hall_ventilation', 'OFF');

INSERT INTO automation_rules (sensor_name, metric_name, operator, threshold, actuator_name, action_value) 
VALUES ('air_quality_pm25', 'pm10_ug_m3', '>', 26, 'hall_ventilation', 'ON');

INSERT INTO automation_rules (sensor_name, metric_name, operator, threshold, actuator_name, action_value) 
VALUES ('air_quality_pm25', 'pm10_ug_m3', '<', 24, 'hall_ventilation', 'OFF');

INSERT INTO automation_rules (sensor_name, metric_name, operator, threshold, actuator_name, action_value) 
VALUES ('air_quality_voc', 'voc_ppb', '>', 242, 'hall_ventilation', 'ON');

INSERT INTO automation_rules (sensor_name, metric_name, operator, threshold, actuator_name, action_value) 
VALUES ('air_quality_voc', 'voc_ppb', '<', 240, 'hall_ventilation', 'OFF');

INSERT INTO automation_rules (sensor_name, metric_name, operator, threshold, actuator_name, action_value) 
VALUES ('air_quality_voc', 'co2e_ppm', '>', 505, 'hall_ventilation', 'ON');

INSERT INTO automation_rules (sensor_name, metric_name, operator, threshold, actuator_name, action_value) 
VALUES ('air_quality_voc', 'co2e_ppm', '<', 499, 'hall_ventilation', 'OFF');
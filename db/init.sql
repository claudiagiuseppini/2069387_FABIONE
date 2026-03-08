-- 1. CREAZIONE DATABASE E UTENTE
CREATE DATABASE IF NOT EXISTS mars_iot;
USE mars_iot;

-- Creiamo l'utente se non esiste e assegniamo i permessi
CREATE USER IF NOT EXISTS 'user_mars'@'%' IDENTIFIED BY 'password_mars';
GRANT SELECT, INSERT, UPDATE, DELETE ON mars_iot.* TO 'user_mars'@'%';
FLUSH PRIVILEGES;

-- 2. CREAZIONE TABELLA
CREATE TABLE IF NOT EXISTS automation_rules (
    id INT AUTO_INCREMENT PRIMARY KEY,
    sensor_name VARCHAR(255) NOT NULL,
    metric_name VARCHAR(255) NOT NULL,
    operator VARCHAR(2) NOT NULL,      -- <, <=, =, >, >=
    threshold FLOAT NOT NULL,
    actuator_name VARCHAR(255) NOT NULL,
    action_value VARCHAR(10) NOT NULL, -- ON / OFF
    enabled BOOLEAN DEFAULT TRUE
);

-- 3. INSERIMENTO REGOLE
INSERT INTO automation_rules 
    (sensor_name, metric_name, operator, threshold, actuator_name, action_value) 
VALUES 
    ('greenhouse_temperature', 'temperature_c', '>', 27, 'cooling_fan', 'ON'),
    ('greenhouse_temperature', 'temperature_c', '<', 23, 'cooling_fan', 'OFF'),
    ('entrance_humidity', 'humidity_pct', '<', 28, 'entrance_humidifier', 'ON'),
    ('entrance_humidity', 'humidity_pct', '>', 31, 'entrance_humidifier', 'OFF'),
    ('co2_hall', 'co2_ppm', '>', 1300.0, 'hall_ventilation', 'ON'),
    ('co2_hall', 'co2_ppm', '<', 1280.0, 'hall_ventilation', 'OFF'),
    ('corridor_pressure', 'pressure_kpa', '<', 100, 'hall_ventilation', 'ON'),
    ('corridor_pressure', 'pressure_kpa', '>', 101, 'hall_ventilation', 'OFF'),
    ('air_quality_pm25', 'pm1_ug_m3', '>', 15, 'hall_ventilation', 'ON'),
    ('air_quality_pm25', 'pm1_ug_m3', '<', 12, 'hall_ventilation', 'OFF'),
    ('air_quality_pm25', 'pm25_ug_m3', '>', 18, 'hall_ventilation', 'ON'),
    ('air_quality_pm25', 'pm25_ug_m3', '<', 15, 'hall_ventilation', 'OFF'),
    ('air_quality_pm25', 'pm10_ug_m3', '>', 26, 'hall_ventilation', 'ON'),
    ('air_quality_pm25', 'pm10_ug_m3', '<', 24, 'hall_ventilation', 'OFF'),
    ('air_quality_voc', 'voc_ppb', '>', 242, 'hall_ventilation', 'ON'),
    ('air_quality_voc', 'voc_ppb', '<', 240, 'hall_ventilation', 'OFF'),
    ('air_quality_voc', 'co2e_ppm', '>', 505, 'hall_ventilation', 'ON'),
    ('air_quality_voc', 'co2e_ppm', '<', 499, 'hall_ventilation', 'OFF');
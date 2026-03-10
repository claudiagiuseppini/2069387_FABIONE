from pathlib import Path

# global variables
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
DEFAULT_RULES_FILE = Path(__file__).parent / "default_rules.json"

DEFAULT_ACTUATORS = {
    "cooling_fan": "OFF",
    "entrance_humidifier": "OFF",
    "hall_ventilation": "OFF",
    "habitat_heater": "OFF"
}
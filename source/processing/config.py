import operator

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

OPERATORS = {
    '>': operator.gt,
    '<': operator.lt,
    '>=': operator.ge,
    '<=': operator.le,
    '=': operator.eq
}
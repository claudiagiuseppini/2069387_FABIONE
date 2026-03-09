import threading
from config import DEFAULT_ACTUATORS

latest_state = {}
event_log = []
actuators_state = {**DEFAULT_ACTUATORS}

state_lock = threading.Lock()
event_lock = threading.Lock()
actuator_lock = threading.Lock()
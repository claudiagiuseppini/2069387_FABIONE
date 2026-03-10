import threading
from config import DEFAULT_ACTUATORS

'''Acts as the 'Single Source of Truth' for the system, managing in-memory 
storage for the latest sensor metrics, event logs, and actuator states.
Uses threading locks to ensure thread-safe concurrent access between 
API endpoints and background worker threads'''

latest_state = {}
event_log = []
actuators_state = {**DEFAULT_ACTUATORS}

state_lock = threading.Lock()
event_lock = threading.Lock()
actuator_lock = threading.Lock()
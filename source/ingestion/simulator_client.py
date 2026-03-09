# simulator_client.py
import requests
from config import SIMULATOR_URL

def get_sensors_list():
    '''Retrieves the list of available sensors from the habitat simulator.'''
    try:
        r = requests.get(f"{SIMULATOR_URL}/api/sensors", timeout=10)
        return r.json().get("sensors", []) if r.status_code == 200 else []
    except: return ["greenhouse_temperature", "hydroponic_ph", "water_tank_level"]

def get_telemetry_list():
    '''Retrieves the list of available telemetry topics from the habitat simulator'''
    try:
        r = requests.get(f"{SIMULATOR_URL}/api/telemetry/topics", timeout=10)
        return r.json().get("topics", []) if r.status_code == 200 else []
    except: return []
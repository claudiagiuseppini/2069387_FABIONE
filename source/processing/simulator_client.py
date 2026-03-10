import requests
from config import SIMULATOR_URL

def send_actuator_command(actuator_id: str, command: str):
    '''uses simulator API to activate/deactivate actuators based on it's agruments'''
    try:
        # sends simulator api message to update the selected actuator
        response = requests.post(
            f"{SIMULATOR_URL}/api/actuators/{actuator_id}",
            json={"state": command},
            timeout=5
        )
        if response.status_code in (200, 201):
            print(f"✅ Command sent: {actuator_id} -> {command}", flush=True)
        else:
            print(f"❌ Error on command {actuator_id}: status={response.status_code}", flush=True)
    except Exception as e:
        print(f"❌ Error on REST request to actuator {actuator_id}: {e}", flush=True)
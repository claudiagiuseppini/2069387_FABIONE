import requests
from config import SIMULATOR_URL

def send_actuator_command(actuator_id: str, command: str):
    try:
        response = requests.post(
            f"{SIMULATOR_URL}/api/actuators/{actuator_id}",
            json={"state": command},
            timeout=5
        )
        if response.status_code in (200, 201):
            print(f"⚙️ Comando inviato con successo: {actuator_id} -> {command}", flush=True)
        else:
            print(f"❌ Errore comando {actuator_id}: status={response.status_code}", flush=True)
    except Exception as e:
        print(f"❌ Errore richiesta REST verso attuatore {actuator_id}: {e}", flush=True)
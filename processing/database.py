import mysql.connector
from config import DB_CONF

def get_db_connection():
    try:
        return mysql.connector.connect(**DB_CONF)
    except Exception as e:
        print(f"❌ Errore connessione DB: {e}", flush=True)
        return None

def get_rules_from_db(sensor_id: str):
    conn = get_db_connection()
    rules = []
    if not conn: return rules

    try:
        cursor = conn.cursor(dictionary=True)
        query = """
            SELECT id, metric_name, operator, threshold, actuator_name, action_value
            FROM automation_rules
            WHERE sensor_name = %s AND enabled = TRUE
        """
        cursor.execute(query, (sensor_id,))
        rules = cursor.fetchall()
        cursor.close()
    except Exception as e:
        print(f"⚠️ Errore lettura regole SQL: {e}", flush=True)
    finally:
        conn.close()
    return rules
import mysql.connector
from config import DB_CONF

def get_db_connection():
    '''Establishes a connection with the database'''
    try:
        return mysql.connector.connect(**DB_CONF)
    except Exception as e:
        print(f"❌ Error connecting to DB: {e}", flush=True)
        return None

def get_rules_from_db(sensor_id: str):
    '''Interrogates database and gets the rules for actuator activation'''

    # establishes db connection and variables
    conn = get_db_connection()
    rules = []
    if not conn: return rules

    try:
        cursor = conn.cursor(dictionary=True)

        # defines query to get all the enabled rules for the selected sensor
        query = """
            SELECT id, metric_name, operator, threshold, actuator_name, action_value
            FROM automation_rules
            WHERE sensor_name = %s AND enabled = TRUE
        """

        # execute query and return the result
        cursor.execute(query, (sensor_id,))
        rules = cursor.fetchall()
        cursor.close()
    except Exception as e:
        print(f"❌ Error reading SQL rules: {e}", flush=True)
    finally:
        conn.close()
    return rules
import mysql.connector
from config import DB_CONF

def get_db_connection():
    '''open connection with the database'''
    try:
        return mysql.connector.connect(**DB_CONF)
    except Exception as e:
        print(f"❌ Error connecting to DB: {e}", flush=True)
        return None
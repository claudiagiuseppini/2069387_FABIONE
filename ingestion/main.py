# main.py
from fastapi import FastAPI
from contextlib import asynccontextmanager
from broker import conn_poll, conn_telemetry, connect_stomp
from workers import start_workers

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Inizializzazione
    connect_stomp(conn_poll, "POLLING")
    connect_stomp(conn_telemetry, "TELEMETRY")
    start_workers()
    yield
    # Cleanup
    if conn_poll.is_connected(): conn_poll.disconnect()
    if conn_telemetry.is_connected(): conn_telemetry.disconnect()

app = FastAPI(title="Mars Ingestion Service", lifespan=lifespan)

@app.get("/health")
def health():
    return {
        "status": "ingestion alive",
        "broker_poll_connected": conn_poll.is_connected(),
        "broker_telemetry_connected": conn_telemetry.is_connected()
    }
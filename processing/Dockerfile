FROM python:3.11-slim

WORKDIR /app

# Installazione dipendenze
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copia del codice
COPY main.py .

# Comando di avvio
CMD ["python", "main.py"]
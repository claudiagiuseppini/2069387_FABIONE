FROM python:3.11-slim

WORKDIR /app

# Installazione dipendenze
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copia del codice
COPY . .

# Comando di avvio
CMD ["python", "main.py"]
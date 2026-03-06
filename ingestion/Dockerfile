# Usa un'immagine Python ufficiale e leggera
FROM python:3.11-alpine

# Imposta la directory di lavoro dentro il container
WORKDIR /app

# Copia il file delle dipendenze
COPY requirements.txt .

# Installa le librerie necessarie
RUN pip install --no-cache-dir -r requirements.txt

# Copia il resto del codice sorgente
COPY . .

# Comando per avviare il servizio
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
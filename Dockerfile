FROM nazhg/hypercycle-eliza:latest

LABEL PERSIST_VOLUME=1
LABEL description="Eliza bot AIM."
LABEL ENV_VARS="PORT=8001;"

WORKDIR /app

# Instalar Python, pip y virtualenv
RUN apt-get update && apt-get install -y python3 python3-pip python3-venv git && rm -rf /var/lib/apt/lists/*

# Crear entorno virtual e instalar dependencias
RUN python3 -m venv venv
ENV PATH="/app/venv/bin:$PATH"

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY server.py .

CMD ["python", "server.py"]

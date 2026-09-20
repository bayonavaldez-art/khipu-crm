# Imagen de la aplicación — Khipu CRM Académico-Comercial
FROM python:3.12-slim

WORKDIR /app

# Dependencias primero (aprovecha la caché de capas)
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Código y artefactos de IA (modelos entrenados)
COPY app/ ./app/
COPY ml/ ./ml/
COPY static/ ./static/

# No correr como root
RUN useradd -m khipu && chown -R khipu:khipu /app
USER khipu

EXPOSE 8000
CMD ["sh", "-c", "uvicorn app.main:app --host 0.0.0.0 --port ${PORT:-8000}"]

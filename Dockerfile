# Multi-stage Dockerfile für Paperless AutoFields
# Optimiert für UGREEN NAS - unterstützt AMD64 und ARM64

FROM python:3.11-slim as base

# Labels für GitHub Container Registry
LABEL org.opencontainers.image.source="https://github.com/baronblk/paperless-autofields"
LABEL org.opencontainers.image.description="Paperless-NGX AutoFields - Automatische Felderkennung für Custom Fields"
LABEL org.opencontainers.image.version="latest"
LABEL org.opencontainers.image.authors="baronblk"
LABEL org.opencontainers.image.licenses="MIT"

# Umgebungsvariablen
ENV PYTHONUNBUFFERED=1
ENV PYTHONDONTWRITEBYTECODE=1
ENV PIP_NO_CACHE_DIR=1
ENV PIP_DISABLE_PIP_VERSION_CHECK=1

# System-Dependencies installieren
RUN apt-get update && apt-get install -y \
    --no-install-recommends \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Arbeitsverzeichnis erstellen
WORKDIR /app

# Python-Dependencies kopieren und installieren
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Anwendungscode kopieren
COPY app/ ./app/
COPY patterns.yaml .

# Logs-Verzeichnis erstellen
RUN mkdir -p logs

# Non-root User erstellen für Sicherheit
RUN groupadd -r appuser && useradd -r -g appuser appuser
RUN chown -R appuser:appuser /app
USER appuser

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:${WEB_PORT:-5000}/health || exit 1

# Ports freigeben
EXPOSE 5000

# Standard-Startkommando
CMD ["python", "app/autofill.py"]

# ---

FROM base as web
# Variante für Web-GUI
CMD ["python", "app/webui/gui.py"]

# ---

FROM base as production
# Produktions-Variante mit gunicorn (optional)
RUN pip install --no-cache-dir gunicorn

# Gunicorn-Konfiguration
COPY gunicorn.conf.py .

CMD ["gunicorn", "--config", "gunicorn.conf.py", "app.webui.gui:app"]

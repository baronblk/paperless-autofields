# Docker Deployment Guide

Dieses Dokument beschreibt verschiedene Deployment-Optionen mit Docker für Paperless AutoFields.

## 🐳 Schnellstart

### Mit Docker Compose (Empfohlen)

```bash
# Repository klonen
git clone https://github.com/baronblk/paperless-autofields.git
cd paperless-autofields

# Konfiguration erstellen
cp .env.example .env
nano .env  # Paperless-NGX Einstellungen anpassen

# Container starten
docker-compose up -d

# Logs ansehen
docker-compose logs -f
```

### Mit Docker Run

```bash
# Nur Hauptanwendung
docker run -d \
  --name paperless-autofields \
  --env-file .env \
  -v $(pwd)/patterns.yaml:/app/patterns.yaml \
  -v $(pwd)/logs:/app/logs \
  --restart unless-stopped \
  ghcr.io/baronblk/paperless-autofields:latest

# Mit Web-Interface
docker run -d \
  --name paperless-autofields-web \
  --env-file .env \
  -p 5000:5000 \
  -v $(pwd)/patterns.yaml:/app/patterns.yaml \
  -v $(pwd)/logs:/app/logs \
  --restart unless-stopped \
  ghcr.io/baronblk/paperless-autofields:web
```

## 🏗️ Build-Varianten

### Standard Build

```bash
# Für aktuelle Architektur
docker build -t paperless-autofields:latest .

# Multi-Architecture (AMD64 + ARM64)
docker buildx build --platform linux/amd64,linux/arm64 \
  -t paperless-autofields:latest .
```

### Produktions-Build mit Gunicorn

```bash
docker build --target production -t paperless-autofields:prod .
```

## 🔧 Konfiguration

### Umgebungsvariablen

| Variable | Beschreibung | Standard | Erforderlich |
|----------|--------------|----------|--------------|
| `PAPERLESS_API_URL` | Paperless-NGX API Endpoint | `http://localhost:8000` | ✅ |
| `PAPERLESS_API_TOKEN` | API Token | - | ✅ |
| `DOCUMENT_TYPE` | Dokumenttyp für Verarbeitung | `Rechnung` | ❌ |
| `RUN_INTERVAL` | Verarbeitungsintervall (Sekunden) | `300` | ❌ |
| `WEB_PORT` | Port für Web-Interface | `5000` | ❌ |
| `LOG_LEVEL` | Logging Level | `INFO` | ❌ |

### Volume Mounts

```yaml
volumes:
  # Pattern-Datei (Live-Editing)
  - ./patterns.yaml:/app/patterns.yaml
  
  # Logs persistent speichern
  - ./logs:/app/logs
  
  # Konfiguration (Read-Only)
  - ./.env:/app/.env:ro
```

## 🌐 Netzwerk-Konfiguration

### Mit existierendem Paperless-NGX

```yaml
# docker-compose.yml
version: '3.8'

services:
  paperless-autofields:
    image: ghcr.io/baronblk/paperless-autofields:latest
    networks:
      - paperless
    environment:
      - PAPERLESS_API_URL=http://paperless-ngx:8000
    depends_on:
      - paperless-ngx

networks:
  paperless:
    external: true  # Nutzt bestehendes Netzwerk
```

### Standalone mit Port-Mapping

```yaml
services:
  paperless-autofields-web:
    ports:
      - "5000:5000"  # Web-Interface
    environment:
      - PAPERLESS_API_URL=http://host.docker.internal:8000
```

## 🏥 Health Checks

### Docker Health Check

```dockerfile
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:${WEB_PORT:-5000}/health || exit 1
```

### Manueller Health Check

```bash
# Container Health Status
docker inspect --format='{{.State.Health.Status}}' paperless-autofields

# Application Health
curl -f http://localhost:5000/health
```

## 📊 Monitoring

### Container-Logs

```bash
# Live-Logs aller Services
docker-compose logs -f

# Nur Hauptanwendung
docker-compose logs -f paperless-autofields

# Letzten 100 Zeilen
docker-compose logs --tail=100 paperless-autofields
```

### Application-Logs

```bash
# In Container
docker exec paperless-autofields tail -f /app/logs/paperless-autofields.log

# Vom Host (bei Volume Mount)
tail -f ./logs/paperless-autofields.log
```

### Resource Monitoring

```bash
# Container Stats
docker stats paperless-autofields

# Detaillierte Informationen
docker exec paperless-autofields ps aux
docker exec paperless-autofields df -h
```

## 🔄 Updates

### Rolling Update

```bash
# Neue Version pullen
docker-compose pull

# Services neu starten
docker-compose up -d

# Alte Images entfernen
docker image prune
```

### Mit Downtime

```bash
# Services stoppen
docker-compose down

# Neue Version starten
docker-compose up -d
```

## 🛠️ Troubleshooting

### Häufige Probleme

#### 1. API-Verbindungsfehler

```bash
# Test der API-Verbindung
docker exec paperless-autofields curl -H "Authorization: Token YOUR_TOKEN" \
  http://paperless-ngx:8000/api/documents/?page_size=1

# Netzwerk prüfen
docker exec paperless-autofields nslookup paperless-ngx
```

#### 2. Permission-Probleme

```bash
# Container mit Root starten (Debug)
docker run -it --entrypoint /bin/bash paperless-autofields:latest

# File-Permissions prüfen
docker exec paperless-autofields ls -la /app/
```

#### 3. Memory-Probleme

```bash
# Memory-Limits setzen
docker run --memory=512m --memory-swap=1g paperless-autofields:latest

# Memory-Verbrauch überwachen
docker stats --no-stream paperless-autofields
```

### Debug-Container

```bash
# Interaktiver Debug-Container
docker run -it --rm \
  --env-file .env \
  -v $(pwd)/patterns.yaml:/app/patterns.yaml \
  paperless-autofields:latest /bin/bash

# Im Container testen
python app/autofill.py --once
python app/webui/gui.py
```

## 🔧 Entwicklung

### Development Setup

```bash
# Development Image bauen
docker build --target base -t paperless-autofields:dev .

# Mit Source-Code Mount für Live-Reload
docker run -it --rm \
  -v $(pwd)/app:/app/app \
  -v $(pwd)/patterns.yaml:/app/patterns.yaml \
  -p 5000:5000 \
  paperless-autofields:dev \
  python app/webui/gui.py
```

### Tests im Container

```bash
# Test-Container
docker run --rm \
  -v $(pwd):/workspace \
  -w /workspace \
  python:3.11-slim \
  bash -c "pip install -r requirements.txt -r requirements-dev.txt && pytest"
```

## 📦 Multi-Stage Builds

Das Dockerfile nutzt Multi-Stage Builds für optimale Images:

- **base**: Hauptanwendung
- **web**: Web-Interface Variante  
- **production**: Produktions-Build mit Gunicorn

```bash
# Spezifische Stage bauen
docker build --target web -t paperless-autofields:web .
docker build --target production -t paperless-autofields:prod .
```

## 🚀 Produktions-Deployment

### Mit Reverse Proxy (Nginx)

```yaml
# docker-compose.yml
services:
  nginx:
    image: nginx:alpine
    ports:
      - "80:80"
      - "443:443"
    volumes:
      - ./nginx.conf:/etc/nginx/nginx.conf
    depends_on:
      - paperless-autofields-web

  paperless-autofields-web:
    image: ghcr.io/baronblk/paperless-autofields:web
    expose:
      - "5000"
```

### SSL/TLS mit Let's Encrypt

```yaml
services:
  certbot:
    image: certbot/certbot
    volumes:
      - ./data/certbot/conf:/etc/letsencrypt
      - ./data/certbot/www:/var/www/certbot
```

### Backup Strategy

```bash
# Patterns und Logs sichern
tar -czf backup-$(date +%Y%m%d).tar.gz patterns.yaml logs/

# Automatisches Backup (Cron)
0 2 * * * cd /opt/paperless-autofields && tar -czf backup-$(date +\%Y\%m\%d).tar.gz patterns.yaml logs/
```

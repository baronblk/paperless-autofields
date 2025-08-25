# UGREEN NAS Deployment

Anleitung für das Deployment von Paperless AutoFields auf einem UGREEN NAS.

## Voraussetzungen

- UGREEN NAS mit Docker-Unterstützung
- Paperless-NGX läuft bereits auf dem NAS oder ist erreichbar
- Zugang zum NAS-Terminal oder Portainer

## Quick Start

### 1. Dateien auf das NAS kopieren

```bash
# Auf dem NAS, erstelle Arbeitsverzeichnis
mkdir -p /volume1/docker/paperless-autofields
cd /volume1/docker/paperless-autofields

# Kopiere die Konfigurationsdateien
wget https://raw.githubusercontent.com/baronblk/paperless-autofields/main/docker-compose.nas.yml
wget https://raw.githubusercontent.com/baronblk/paperless-autofields/main/.env.example
wget https://raw.githubusercontent.com/baronblk/paperless-autofields/main/patterns.yaml
```

### 2. Konfiguration

```bash
# Erstelle .env-Datei
cp .env.example .env

# Bearbeite die .env-Datei
vi .env
```

Wichtige Einstellungen:
```bash
PAPERLESS_API_URL=http://192.168.2.12:8810  # Deine Paperless-NGX URL
PAPERLESS_API_TOKEN=dein_api_token_hier      # Aus Paperless-NGX Settings > API
DOCUMENT_TYPE=Rechnung                       # Zu verarbeitender Dokumenttyp
WEB_PORT=5001                               # Port für Web-Interface
```

### 3. Container starten

```bash
# Mit Docker Compose
docker-compose -f docker-compose.nas.yml up -d

# Oder nur Hauptservice ohne Web-Interface
docker run -d --name paperless-autofields \
  --env-file .env \
  --restart unless-stopped \
  -v $(pwd)/logs:/app/logs \
  -v $(pwd)/patterns.yaml:/app/patterns.yaml:ro \
  ghcr.io/baronblk/paperless-autofields:latest
```

### 4. Logs überprüfen

```bash
# Docker Compose Logs
docker-compose -f docker-compose.nas.yml logs -f

# Einzelner Container
docker logs -f paperless-autofields

# Log-Datei direkt
tail -f logs/paperless-autofields.log
```

## Portainer Setup

Falls Sie Portainer verwenden:

1. **Stack erstellen:**
   - Gehen Sie zu "Stacks" → "Add stack"
   - Name: `paperless-autofields`
   - Repository URL: `https://github.com/baronblk/paperless-autofields`
   - Compose path: `docker-compose.nas.yml`

2. **Environment Variables:**
   ```
   PAPERLESS_API_URL=http://ihre-paperless-url:8000
   PAPERLESS_API_TOKEN=ihr_token
   WEB_PORT=5001
   ```

3. **Deploy:** Klicken Sie "Deploy the stack"

## Services

### Hauptservice (paperless-autofields)
- **Image:** `ghcr.io/baronblk/paperless-autofields:latest`
- **Funktion:** Automatische Verarbeitung von Dokumenten
- **Port:** Keiner (läuft im Hintergrund)
- **Volumes:** 
  - `./logs:/app/logs` (Logs)
  - `./patterns.yaml:/app/patterns.yaml:ro` (Pattern-Konfiguration)

### Web-Interface (optional)
- **Image:** `ghcr.io/baronblk/paperless-autofields:web`
- **Funktion:** Grafische Benutzeroberfläche
- **Port:** `5001:5000` (oder Ihr gewählter Port)
- **URL:** `http://nas-ip:5001`

## Konfiguration anpassen

### Pattern-Datei bearbeiten
```bash
vi patterns.yaml
```

Nach Änderungen Container neustarten:
```bash
docker-compose -f docker-compose.nas.yml restart
```

### Neue Container-Version holen
```bash
docker-compose -f docker-compose.nas.yml pull
docker-compose -f docker-compose.nas.yml up -d
```

## Überwachung

### Health Checks
```bash
# Service-Status prüfen
docker-compose -f docker-compose.nas.yml ps

# Health-Status einzeln
docker inspect --format='{{.State.Health.Status}}' paperless-autofields
```

### API-Test
```bash
# In Container ausführen
docker exec paperless-autofields python -c "
from app.api import PaperlessAPI
from app.config import Config
config = Config()
api = PaperlessAPI(config.paperless_api_url, config.paperless_api_token)
print('✅ API-Verbindung erfolgreich!')
"
```

## Fehlerbehebung

### Häufige Probleme

1. **401 Unauthorized**
   - API-Token prüfen
   - Paperless-NGX URL korrekt?

2. **Container startet nicht**
   - Logs prüfen: `docker logs paperless-autofields`
   - .env-Datei korrekt formatiert?

3. **Keine Dokumente gefunden**
   - DOCUMENT_TYPE in .env prüfen
   - Paperless-NGX erreichbar?

### Debug-Modus
```bash
# Container im Debug-Modus starten
docker run --rm -it --env-file .env \
  ghcr.io/baronblk/paperless-autofields:latest \
  python -m app.cli list-docs --limit 5
```

## Updates

```bash
# Neue Version holen
docker pull ghcr.io/baronblk/paperless-autofields:latest

# Container neustarten
docker-compose -f docker-compose.nas.yml up -d
```

## Backup

```bash
# Konfiguration sichern
tar czf paperless-autofields-backup.tar.gz .env patterns.yaml logs/
```

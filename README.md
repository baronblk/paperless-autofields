# Paperless-NGX AutoFields

Ein professionelles Python-basiertes Sidecar-Modul für Paperless-NGX zur automatischen Extraktion und Verarbeitung von Dokumentfeldern mittels OCR und RegEx.

## 🎯 Features

- **Automatische Felderkennung**: Extraktion von Rechnungsnummer, Zahlungsziel, IBAN und weiteren Feldern
- **Multi-Platform Docker**: Unterstützung für amd64 und arm64 (Raspberry Pi kompatibel)
- **Web-GUI**: Flask-basierte Benutzeroberfläche zur Konfiguration und Überwachung
- **Live-Reload**: Dynamisches Nachladen von Regex-Patterns ohne Container-Neustart
- **Modular & Erweiterbar**: Saubere Trennung von Logik, API und UI-Komponenten
- **Umfassendes Logging**: Strukturierte Logs mit Rotation für Debugging und Monitoring

## 🏗️ Architektur

```
paperless-autofields/
├── app/
│   ├── autofill.py         # Hauptlogik mit Endlosschleife
│   ├── api.py              # REST-Kommunikation mit Paperless-NGX
│   ├── config.py           # Konfigurationsmanagement
│   ├── extractor.py        # OCR/Regex-Extraktionslogik
│   └── webui/
│       └── gui.py          # Flask Web-Interface
├── patterns.yaml           # Regex-Pattern-Definitionen
├── docker-compose.yml      # Container-Orchestrierung
└── tests/                  # Unit-Tests mit pytest
```

## 🚀 Quick Start

### Mit Docker Compose (Empfohlen)

1. Repository klonen:
```bash
git clone https://github.com/baronblk/paperless-autofields.git
cd paperless-autofields
```

2. Umgebungsvariablen konfigurieren:
```bash
cp .env.example .env
# .env-Datei bearbeiten
```

3. Container starten:
```bash
docker-compose up -d
```

4. Web-GUI öffnen: `http://localhost:5000`

### Manuelle Installation

1. Python 3.11+ installieren
2. Dependencies installieren:
```bash
pip install -r requirements.txt
```

3. Umgebungsvariablen setzen und starten:
```bash
python app/autofill.py
```

## ⚙️ Konfiguration

### Umgebungsvariablen

| Variable | Beschreibung | Standard |
|----------|--------------|----------|
| `PAPERLESS_API_URL` | Paperless-NGX API-Endpoint | `http://localhost:8000` |
| `PAPERLESS_API_TOKEN` | API-Token für Authentifizierung | - |
| `DOCUMENT_TYPE` | Zu verarbeitender Dokumenttyp | `Rechnung` |
| `RUN_INTERVAL` | Verarbeitungsintervall (Sekunden) | `300` |
| `LOG_LEVEL` | Logging-Level | `INFO` |
| `WEB_PORT` | Port für Web-GUI | `5000` |

### Regex-Patterns

Patterns werden in `patterns.yaml` definiert und können zur Laufzeit über die Web-GUI bearbeitet werden:

```yaml
rechnungsnummer:
  pattern: "Rechnung(?:snummer)?:?\s*([A-Z0-9-]+)"
  description: "Erkennt Rechnungsnummern"
  
zahlungsziel:
  pattern: "(?:Zahlbar bis|Fällig am|Zahlungsziel):?\s*(\d{1,2}\.\d{1,2}\.\d{4})"
  description: "Erkennt Zahlungstermine"
```

## 🧪 Testing

```bash
# Unit-Tests ausführen
pytest tests/

# Mit Coverage
pytest --cov=app tests/

# Spezifische Tests
pytest tests/test_extractor.py -v
```

## 📊 Monitoring

- **Logs**: Verfügbar unter `/app/logs/` im Container
- **Web-GUI**: Live-Monitoring unter `http://localhost:5000/logs`
- **Health Check**: `http://localhost:5000/health`

## 🤝 Contributing

1. Fork des Repositories erstellen
2. Feature-Branch erstellen (`git checkout -b feature/amazing-feature`)
3. Änderungen committen (`git commit -m 'Add amazing feature'`)
4. Branch pushen (`git push origin feature/amazing-feature`)
5. Pull Request erstellen

## 📝 License

Dieses Projekt ist unter der MIT-Lizenz veröffentlicht. Siehe [LICENSE](LICENSE) für Details.

## 🛠️ Entwicklung

### Lokale Entwicklung

```bash
# Development Dependencies installieren
pip install -r requirements-dev.txt

# Pre-commit Hooks installieren
pre-commit install

# Tests im Watch-Mode
pytest-watch
```

### Docker Build

```bash
# Multi-Architecture Build
docker buildx build --platform linux/amd64,linux/arm64 -t paperless-autofields:latest .

# Nur aktuelle Architektur
docker build -t paperless-autofields:latest .
```

## 📞 Support

Bei Fragen oder Problemen:
- GitHub Issues: [Issues](https://github.com/baronblk/paperless-autofields/issues)
- Diskussionen: [Discussions](https://github.com/baronblk/paperless-autofields/discussions)

---

**Hinweis**: Dieses Projekt ist als Sidecar für Paperless-NGX konzipiert und erfordert eine laufende Paperless-NGX-Instanz mit aktivierter API.

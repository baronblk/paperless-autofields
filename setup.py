#!/usr/bin/env python3
"""
Paperless AutoFields Setup Script

Interaktives Setup-Script zur Erstkonfiguration des Systems.
"""

import os
import sys
import subprocess
from pathlib import Path
from typing import Dict, Any
import yaml


def print_banner():
    """Zeigt das Banner an."""
    print("""
╔══════════════════════════════════════════════════════════════╗
║                    Paperless AutoFields                     ║
║                    Setup & Configuration                    ║
╚══════════════════════════════════════════════════════════════╝
    """)


def check_requirements():
    """Prüft die Systemvoraussetzungen."""
    print("🔍 Prüfe Systemvoraussetzungen...")
    
    # Python Version prüfen
    if sys.version_info < (3, 9):
        print("❌ Python 3.9+ erforderlich")
        sys.exit(1)
    
    print(f"✅ Python {sys.version.split()[0]}")
    
    # Docker prüfen (optional)
    try:
        subprocess.run(['docker', '--version'], 
                      capture_output=True, check=True)
        print("✅ Docker verfügbar")
    except (subprocess.CalledProcessError, FileNotFoundError):
        print("⚠️  Docker nicht verfügbar (optional für Entwicklung)")
    
    # Git prüfen
    try:
        subprocess.run(['git', '--version'], 
                      capture_output=True, check=True)
        print("✅ Git verfügbar")
    except (subprocess.CalledProcessError, FileNotFoundError):
        print("⚠️  Git nicht verfügbar")


def get_user_input(prompt: str, default: str = None, 
                  required: bool = True) -> str:
    """Holt Benutzereingabe mit Validierung."""
    while True:
        if default:
            user_input = input(f"{prompt} [{default}]: ").strip()
            if not user_input:
                return default
        else:
            user_input = input(f"{prompt}: ").strip()
        
        if user_input or not required:
            return user_input
        
        if required:
            print("❌ Eingabe erforderlich!")


def get_paperless_config() -> Dict[str, Any]:
    """Sammelt Paperless-NGX Konfiguration."""
    print("\n📝 Paperless-NGX Konfiguration")
    print("-" * 40)
    
    config = {}
    
    config['PAPERLESS_API_URL'] = get_user_input(
        "Paperless-NGX URL", 
        "http://localhost:8000"
    )
    
    config['PAPERLESS_API_TOKEN'] = get_user_input(
        "API Token (aus Paperless-NGX Admin)"
    )
    
    config['DOCUMENT_TYPE'] = get_user_input(
        "Dokumenttyp für Verarbeitung", 
        "Rechnung"
    )
    
    return config


def get_processing_config() -> Dict[str, Any]:
    """Sammelt Verarbeitungskonfiguration."""
    print("\n⚙️  Verarbeitungseinstellungen")
    print("-" * 40)
    
    config = {}
    
    interval = get_user_input(
        "Verarbeitungsintervall (Sekunden)", 
        "300"
    )
    config['RUN_INTERVAL'] = interval
    
    # Validierung
    validate = get_user_input(
        "Extrahierte Werte validieren? (y/n)", 
        "y", 
        required=False
    ).lower()
    config['VALIDATE_EXTRACTED_VALUES'] = str(validate.startswith('y')).lower()
    
    # Skip processed
    skip = get_user_input(
        "Bereits verarbeitete Dokumente überspringen? (y/n)", 
        "y", 
        required=False
    ).lower()
    config['SKIP_PROCESSED_DOCUMENTS'] = str(skip.startswith('y')).lower()
    
    return config


def get_web_config() -> Dict[str, Any]:
    """Sammelt Web-GUI Konfiguration."""
    print("\n🌐 Web-Interface Einstellungen")
    print("-" * 40)
    
    config = {}
    
    enable_web = get_user_input(
        "Web-Interface aktivieren? (y/n)", 
        "y", 
        required=False
    ).lower()
    
    if enable_web.startswith('y'):
        config['WEB_PORT'] = get_user_input("Web-Port", "5000")
        config['WEB_HOST'] = get_user_input("Web-Host", "0.0.0.0")
    
    return config


def get_logging_config() -> Dict[str, Any]:
    """Sammelt Logging-Konfiguration."""
    print("\n📋 Logging-Einstellungen")
    print("-" * 40)
    
    config = {}
    
    config['LOG_LEVEL'] = get_user_input(
        "Log-Level (DEBUG/INFO/WARNING/ERROR)", 
        "INFO"
    ).upper()
    
    config['LOG_FILE'] = get_user_input(
        "Log-Datei Pfad", 
        "logs/paperless-autofields.log"
    )
    
    return config


def create_env_file(config: Dict[str, Any]) -> None:
    """Erstellt die .env-Datei."""
    print("\n📄 Erstelle .env-Datei...")
    
    env_content = [
        "# Paperless AutoFields Configuration",
        "# Generiert durch setup.py",
        "",
        "# Paperless-NGX API Configuration",
        f"PAPERLESS_API_URL={config.get('PAPERLESS_API_URL', 'http://localhost:8000')}",
        f"PAPERLESS_API_TOKEN={config.get('PAPERLESS_API_TOKEN', '')}",
        "",
        "# Document Processing",
        f"DOCUMENT_TYPE={config.get('DOCUMENT_TYPE', 'Rechnung')}",
        f"RUN_INTERVAL={config.get('RUN_INTERVAL', '300')}",
        "",
        "# Processing Options",
        f"VALIDATE_EXTRACTED_VALUES={config.get('VALIDATE_EXTRACTED_VALUES', 'true')}",
        f"SKIP_PROCESSED_DOCUMENTS={config.get('SKIP_PROCESSED_DOCUMENTS', 'true')}",
        "",
        "# Web UI",
        f"WEB_PORT={config.get('WEB_PORT', '5000')}",
        f"WEB_HOST={config.get('WEB_HOST', '0.0.0.0')}",
        "",
        "# Logging",
        f"LOG_LEVEL={config.get('LOG_LEVEL', 'INFO')}",
        f"LOG_FILE={config.get('LOG_FILE', 'logs/paperless-autofields.log')}",
        f"LOG_MAX_SIZE={config.get('LOG_MAX_SIZE', '10MB')}",
        f"LOG_BACKUP_COUNT={config.get('LOG_BACKUP_COUNT', '5')}",
        "",
        "# Pattern File",
        f"PATTERN_FILE={config.get('PATTERN_FILE', 'patterns.yaml')}",
        ""
    ]
    
    with open('.env', 'w', encoding='utf-8') as f:
        f.write('\n'.join(env_content))
    
    print("✅ .env-Datei erstellt")


def setup_directories() -> None:
    """Erstellt notwendige Verzeichnisse."""
    print("\n📁 Erstelle Verzeichnisse...")
    
    directories = [
        'logs',
        'app/webui/templates',
        'tests',
        'docs'
    ]
    
    for directory in directories:
        Path(directory).mkdir(parents=True, exist_ok=True)
        print(f"✅ {directory}/")


def install_dependencies() -> None:
    """Installiert Python-Dependencies."""
    print("\n📦 Installiere Dependencies...")
    
    try:
        subprocess.run([
            sys.executable, '-m', 'pip', 'install', '-r', 'requirements.txt'
        ], check=True)
        print("✅ Production Dependencies installiert")
        
        # Optional: Development Dependencies
        install_dev = get_user_input(
            "Development Dependencies installieren? (y/n)", 
            "n", 
            required=False
        ).lower()
        
        if install_dev.startswith('y'):
            subprocess.run([
                sys.executable, '-m', 'pip', 'install', 
                '-r', 'requirements-dev.txt'
            ], check=True)
            print("✅ Development Dependencies installiert")
            
    except subprocess.CalledProcessError as e:
        print(f"❌ Fehler bei Installation: {e}")
        sys.exit(1)


def test_configuration(config: Dict[str, Any]) -> bool:
    """Testet die Konfiguration."""
    print("\n🧪 Teste Konfiguration...")
    
    try:
        # Importiere nach Installation
        sys.path.append(str(Path('app').resolve()))
        from config import Config
        from api import PaperlessAPI
        
        # Temporäre Umgebungsvariablen setzen
        for key, value in config.items():
            os.environ[key] = str(value)
        
        # Config testen
        app_config = Config()
        print("✅ Konfiguration gültig")
        
        # API-Verbindung testen
        api = PaperlessAPI(
            app_config.paperless_api_url, 
            app_config.paperless_api_token
        )
        print("✅ API-Verbindung erfolgreich")
        
        return True
        
    except Exception as e:
        print(f"❌ Konfigurationsfehler: {e}")
        return False


def create_systemd_service() -> None:
    """Erstellt systemd Service-Datei (Linux)."""
    if os.name != 'posix':
        return
    
    create_service = get_user_input(
        "Systemd Service erstellen? (y/n)", 
        "n", 
        required=False
    ).lower()
    
    if not create_service.startswith('y'):
        return
    
    print("\n🔧 Erstelle systemd Service...")
    
    current_dir = Path.cwd().resolve()
    python_path = sys.executable
    
    service_content = f"""[Unit]
Description=Paperless AutoFields
After=network.target

[Service]
Type=simple
User={os.getenv('USER', 'paperless')}
WorkingDirectory={current_dir}
Environment=PATH={os.environ.get('PATH')}
ExecStart={python_path} {current_dir}/app/autofill.py
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
"""
    
    service_file = Path('paperless-autofields.service')
    with open(service_file, 'w') as f:
        f.write(service_content)
    
    print(f"✅ Service-Datei erstellt: {service_file}")
    print(f"   Installieren mit:")
    print(f"   sudo cp {service_file} /etc/systemd/system/")
    print(f"   sudo systemctl enable paperless-autofields")
    print(f"   sudo systemctl start paperless-autofields")


def print_next_steps():
    """Zeigt nächste Schritte an."""
    print("\n🎉 Setup abgeschlossen!")
    print("\n📋 Nächste Schritte:")
    print("=" * 50)
    print("1. Konfiguration prüfen:")
    print("   python app/cli.py list-patterns")
    print("")
    print("2. Einzelnes Dokument testen:")
    print("   python app/cli.py process <DOKUMENT_ID> --dry-run")
    print("")
    print("3. Hauptanwendung starten:")
    print("   python app/autofill.py")
    print("")
    print("4. Web-Interface starten:")
    print("   python app/webui/gui.py")
    print("   Dann öffnen: http://localhost:5000")
    print("")
    print("5. Docker verwenden:")
    print("   docker-compose up -d")
    print("")
    print("📚 Dokumentation:")
    print("   README.md - Vollständige Anleitung")
    print("   patterns.yaml - Pattern-Konfiguration")
    print("   .env - Umgebungsvariablen")


def main():
    """Hauptfunktion des Setup-Scripts."""
    print_banner()
    
    print("Willkommen beim Paperless AutoFields Setup!")
    print("Dieses Script hilft Ihnen bei der Erstkonfiguration.\n")
    
    # Voraussetzungen prüfen
    check_requirements()
    
    # Konfiguration sammeln
    config = {}
    config.update(get_paperless_config())
    config.update(get_processing_config())
    config.update(get_web_config())
    config.update(get_logging_config())
    
    # Setup durchführen
    setup_directories()
    create_env_file(config)
    
    # Dependencies installieren
    install_deps = get_user_input(
        "Dependencies jetzt installieren? (y/n)", 
        "y", 
        required=False
    ).lower()
    
    if install_deps.startswith('y'):
        install_dependencies()
        
        # Konfiguration testen
        if test_configuration(config):
            print("✅ Setup erfolgreich!")
        else:
            print("⚠️  Setup abgeschlossen, aber Konfiguration fehlerhaft")
            print("   Bitte überprüfen Sie die .env-Datei")
    
    # Systemd Service (Linux)
    create_systemd_service()
    
    # Abschluss
    print_next_steps()


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n❌ Setup abgebrochen")
        sys.exit(1)
    except Exception as e:
        print(f"\n\n❌ Unerwarteter Fehler: {e}")
        sys.exit(1)

"""
Paperless AutoFields - Configuration Management

Dieses Modul verwaltet die Konfiguration der Anwendung durch
Umgebungsvariablen und .env-Dateien.
"""

import os
from pathlib import Path
from typing import Optional
from dotenv import load_dotenv
from loguru import logger


class Config:
    """Konfigurationsmanagement für Paperless AutoFields."""
    
    def __init__(self, env_file: Optional[str] = None):
        """
        Initialisiert die Konfiguration.
        
        Args:
            env_file: Pfad zur .env-Datei (optional)
        """
        if env_file:
            load_dotenv(env_file)
        else:
            load_dotenv()
            
        self.validate_config()
    
    # Paperless-NGX API Configuration
    @property
    def paperless_api_url(self) -> str:
        """Paperless-NGX API URL."""
        return os.getenv('PAPERLESS_API_URL', 'http://localhost:8000')
    
    @property
    def paperless_api_token(self) -> str:
        """Paperless-NGX API Token."""
        token = os.getenv('PAPERLESS_API_TOKEN')
        if not token:
            raise ValueError("PAPERLESS_API_TOKEN ist erforderlich")
        return token
    
    # Document Processing
    @property
    def document_type(self) -> str:
        """Zu verarbeitender Dokumenttyp."""
        return os.getenv('DOCUMENT_TYPE', 'Rechnung')
    
    @property
    def run_interval(self) -> int:
        """Verarbeitungsintervall in Sekunden."""
        return int(os.getenv('RUN_INTERVAL', '300'))
    
    # Web UI
    @property
    def web_port(self) -> int:
        """Port für Web-GUI."""
        return int(os.getenv('WEB_PORT', '5000'))
    
    @property
    def web_host(self) -> str:
        """Host für Web-GUI."""
        return os.getenv('WEB_HOST', '0.0.0.0')
    
    # Logging
    @property
    def log_level(self) -> str:
        """Logging-Level."""
        return os.getenv('LOG_LEVEL', 'INFO')
    
    @property
    def log_file(self) -> str:
        """Pfad zur Log-Datei."""
        return os.getenv('LOG_FILE', 'logs/paperless-autofields.log')
    
    @property
    def log_max_size(self) -> str:
        """Maximale Größe der Log-Datei."""
        return os.getenv('LOG_MAX_SIZE', '10MB')
    
    @property
    def log_backup_count(self) -> int:
        """Anzahl der Log-Backup-Dateien."""
        return int(os.getenv('LOG_BACKUP_COUNT', '5'))
    
    # Pattern File
    @property
    def pattern_file(self) -> str:
        """Pfad zur Pattern-Datei."""
        return os.getenv('PATTERN_FILE', 'patterns.yaml')
    
    # Processing Options
    @property
    def validate_extracted_values(self) -> bool:
        """Ob extrahierte Werte validiert werden sollen."""
        return os.getenv('VALIDATE_EXTRACTED_VALUES', 'true').lower() == 'true'
    
    @property
    def skip_processed_documents(self) -> bool:
        """Ob bereits verarbeitete Dokumente übersprungen werden sollen."""
        return os.getenv('SKIP_PROCESSED_DOCUMENTS', 'true').lower() == 'true'
    
    def validate_config(self) -> None:
        """Validiert die Konfiguration."""
        try:
            # Prüfe kritische Konfiguration (löst Exception aus wenn nicht
            # vorhanden)
            _ = self.paperless_api_token
            
            # Erstelle Log-Verzeichnis falls nötig
            log_path = Path(self.log_file).parent
            log_path.mkdir(parents=True, exist_ok=True)
            
            # Prüfe Pattern-Datei
            if not Path(self.pattern_file).exists():
                pattern_msg = (f"Pattern-Datei {self.pattern_file} "
                               f"nicht gefunden")
                logger.warning(pattern_msg)
            
            logger.success("Konfiguration erfolgreich validiert")
            
        except Exception as e:
            logger.error(f"Konfigurationsfehler: {e}")
            raise
    
    def get_config_dict(self) -> dict:
        """Gibt alle Konfigurationswerte als Dictionary zurück."""
        return {
            'paperless_api_url': self.paperless_api_url,
            'document_type': self.document_type,
            'run_interval': self.run_interval,
            'web_port': self.web_port,
            'web_host': self.web_host,
            'log_level': self.log_level,
            'log_file': self.log_file,
            'pattern_file': self.pattern_file,
            'validate_extracted_values': self.validate_extracted_values,
            'skip_processed_documents': self.skip_processed_documents,
        }

"""
Paperless AutoFields - Main Application Logic

Hauptmodul mit der Endlosschleife zur automatischen Dokumentverarbeitung.
"""

import time
import sys
from pathlib import Path
from loguru import logger
from config import Config
from api import PaperlessAPI
from extractor import FieldExtractor


class AutoFieldProcessor:
    """Hauptverarbeitung für automatische Felderkennung."""
    
    def __init__(self):
        """Initialisiert den Processor."""
        self.config = Config()
        self.setup_logging()
        
        logger.info("Paperless AutoFields gestartet")
        logger.info(f"Konfiguration: {self.config.get_config_dict()}")
        
        try:
            self.api = PaperlessAPI(
                self.config.paperless_api_url,
                self.config.paperless_api_token
            )
            self.extractor = FieldExtractor(self.config.pattern_file)
            
        except Exception as e:
            logger.error(f"Initialisierungsfehler: {e}")
            sys.exit(1)
    
    def setup_logging(self) -> None:
        """Konfiguriert das Logging."""
        # Entferne Standard-Handler
        logger.remove()
        
        # Konsolen-Logger
        logger.add(
            sys.stdout,
            level=self.config.log_level,
            format="{time:YYYY-MM-DD HH:mm:ss} | {level} | {message}",
            colorize=True
        )
        
        # Datei-Logger mit Rotation
        log_path = Path(self.config.log_file)
        log_path.parent.mkdir(parents=True, exist_ok=True)
        
        logger.add(
            self.config.log_file,
            level=self.config.log_level,
            format="{time:YYYY-MM-DD HH:mm:ss} | {level} | {name} | {message}",
            rotation=self.config.log_max_size,
            retention=self.config.log_backup_count,
            compression="zip"
        )
    
    def process_document(self, document: dict) -> bool:
        """
        Verarbeitet ein einzelnes Dokument.
        
        Args:
            document: Dokument-Daten von der API
            
        Returns:
            True bei erfolgreicher Verarbeitung, False sonst
        """
        document_id = document['id']
        document_title = document.get('title', 'Unbekannt')
        
        logger.info(f"Verarbeite Dokument {document_id}: {document_title}")
        
        # Prüfe ob bereits verarbeitet (falls konfiguriert)
        if self.config.skip_processed_documents:
            existing_fields = self.api.get_document_custom_fields(document_id)
            if existing_fields:
                logger.debug(f"Dokument {document_id} bereits verarbeitet, "
                           f"überspringe")
                return True
        
        # OCR-Inhalt abrufen
        content = self.api.get_document_content(document_id)
        if not content:
            logger.warning(f"Kein OCR-Inhalt für Dokument {document_id}")
            return False
        
        # Felder extrahieren
        extracted_fields = self.extractor.extract_all_fields(content)
        
        if not extracted_fields:
            logger.info(f"Keine Felder in Dokument {document_id} gefunden")
            return True
        
        # Felder validieren und setzen
        success_count = 0
        for field_name, value in extracted_fields.items():
            
            # Validierung falls konfiguriert
            if self.config.validate_extracted_values:
                if not self.extractor.validate_value(field_name, value):
                    logger.warning(f"Validierung fehlgeschlagen für "
                                 f"'{field_name}': '{value}'")
                    continue
                
                # Spezielle IBAN-Validierung
                if field_name.lower() == 'iban':
                    if not self.extractor.validate_iban(value):
                        logger.warning(f"IBAN-Validierung fehlgeschlagen: "
                                     f"'{value}'")
                        continue
            
            # Custom Field setzen
            if self.api.set_custom_field_value(document_id, field_name, value):
                success_count += 1
            else:
                logger.error(f"Fehler beim Setzen von '{field_name}' "
                           f"für Dokument {document_id}")
        
        logger.info(f"Dokument {document_id}: {success_count}/"
                   f"{len(extracted_fields)} Felder erfolgreich gesetzt")
        
        return success_count > 0
    
    def process_all_documents(self) -> int:
        """
        Verarbeitet alle Dokumente des konfigurierten Typs.
        
        Returns:
            Anzahl erfolgreich verarbeiteter Dokumente
        """
        logger.info(f"Starte Verarbeitung für Dokumenttyp: "
                   f"'{self.config.document_type}'")
        
        # Dokumente abrufen
        documents = self.api.get_documents_by_type(self.config.document_type)
        
        if not documents:
            logger.info("Keine Dokumente zum Verarbeiten gefunden")
            return 0
        
        # Dokumente verarbeiten
        processed_count = 0
        for document in documents:
            try:
                if self.process_document(document):
                    processed_count += 1
            except Exception as e:
                logger.error(f"Fehler bei Verarbeitung von Dokument "
                           f"{document['id']}: {e}")
        
        logger.success(f"Verarbeitung abgeschlossen: {processed_count}/"
                      f"{len(documents)} Dokumente erfolgreich verarbeitet")
        
        return processed_count
    
    def run_once(self) -> None:
        """Führt einen einzelnen Verarbeitungslauf durch."""
        start_time = time.time()
        
        try:
            # Patterns neu laden falls geändert
            self.extractor.reload_patterns()
            
            # Dokumente verarbeiten
            processed = self.process_all_documents()
            
            duration = time.time() - start_time
            logger.info(f"Verarbeitungslauf abgeschlossen in {duration:.2f}s, "
                       f"{processed} Dokumente verarbeitet")
            
        except KeyboardInterrupt:
            logger.info("Verarbeitung durch Benutzer unterbrochen")
            raise
        except Exception as e:
            logger.error(f"Fehler während Verarbeitungslauf: {e}")
    
    def run_continuous(self) -> None:
        """Startet die kontinuierliche Verarbeitung."""
        logger.info(f"Starte kontinuierliche Verarbeitung "
                   f"(Intervall: {self.config.run_interval}s)")
        
        try:
            while True:
                self.run_once()
                
                logger.debug(f"Warte {self.config.run_interval} Sekunden "
                           f"bis zum nächsten Lauf...")
                time.sleep(self.config.run_interval)
                
        except KeyboardInterrupt:
            logger.info("Anwendung durch Benutzer beendet")
        except Exception as e:
            logger.error(f"Kritischer Fehler: {e}")
            sys.exit(1)


def main():
    """Haupteinstiegspunkt der Anwendung."""
    try:
        processor = AutoFieldProcessor()
        
        # Prüfe ob einmaliger Lauf oder kontinuierlich
        if len(sys.argv) > 1 and sys.argv[1] == '--once':
            processor.run_once()
        else:
            processor.run_continuous()
            
    except KeyboardInterrupt:
        logger.info("Anwendung beendet")
    except Exception as e:
        logger.error(f"Kritischer Anwendungsfehler: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()

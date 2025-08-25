"""
Paperless AutoFields - OCR/Regex Extraction Logic

Dieses Modul extrahiert Felder aus OCR-Text mittels konfigurierbarer
Regex-Patterns.
"""

import re
import yaml
from pathlib import Path
from typing import Dict, Optional, Any
from loguru import logger


class FieldExtractor:
    """Extrahiert Felder aus Dokumenttext mittels Regex-Patterns."""
    
    def __init__(self, pattern_file: str = "patterns.yaml"):
        """
        Initialisiert den Extraktor.
        
        Args:
            pattern_file: Pfad zur Pattern-Konfigurationsdatei
        """
        self.pattern_file = pattern_file
        self.patterns = {}
        self.load_patterns()
    
    def load_patterns(self) -> None:
        """Lädt Patterns aus der YAML-Datei."""
        try:
            if not Path(self.pattern_file).exists():
                logger.warning(f"Pattern-Datei {self.pattern_file} nicht "
                               f"gefunden, verwende Standard-Patterns")
                self.patterns = self._get_default_patterns()
                return
            
            with open(self.pattern_file, 'r', encoding='utf-8') as f:
                self.patterns = yaml.safe_load(f) or {}
            
            pattern_count = len(self.patterns)
            logger.success(f"Patterns geladen: {pattern_count} Felder "
                           f"verfügbar")
            
        except Exception as e:
            logger.error(f"Fehler beim Laden der Patterns: {e}")
            self.patterns = self._get_default_patterns()
    
    def _get_default_patterns(self) -> Dict[str, Dict[str, str]]:
        """Gibt Standard-Patterns zurück falls Datei nicht verfügbar."""
        return {
            'rechnungsnummer': {
                'pattern': (
                    r'(?i)(?:rechnung(?:s)?(?:nummer|nr\.?)?|'
                    r'invoice(?:\s+)?(?:number|no\.?)?|rg\.?\s?nr\.?)'
                    r'[:\s]*([A-Z0-9][A-Z0-9\-._/]*[A-Z0-9]|[A-Z0-9])'
                ),
                'description': 'Erkennt Rechnungsnummern'
            },
            'zahlungsziel': {
                'pattern': (
                    r'(?i)(?:zahlbar\s+bis|fällig\s+am|zahlungsziel|'
                    r'due\s+date|payment\s+due)[:\s]*'
                    r'(\d{1,2}\.?\d{1,2}\.?\d{2,4}|'
                    r'\d{2,4}-\d{1,2}-\d{1,2})'
                ),
                'description': 'Erkennt Zahlungstermine'
            },
            'betrag': {
                'pattern': (
                    r'(?i)(?:(?:rechnungs)?(?:betrag|summe)|'
                    r'(?:total|gesamt)(?:betrag|summe)?|amount)[:\s]*'
                    r'(?:EUR|€)?\s*(\d{1,3}(?:[.,]\d{3})*[.,]\d{2})'
                ),
                'description': 'Erkennt Rechnungsbeträge'
            }
        }
    
    def extract_field(self, text: str, field_name: str) -> Optional[str]:
        """
        Extrahiert einen spezifischen Feldwert aus dem Text.
        
        Args:
            text: Zu durchsuchender Text
            field_name: Name des zu extrahierenden Feldes
            
        Returns:
            Extrahierter Wert oder None falls nicht gefunden
        """
        if field_name not in self.patterns:
            logger.warning(f"Kein Pattern für Feld '{field_name}' definiert")
            return None
        
        pattern_config = self.patterns[field_name]
        pattern = pattern_config.get('pattern')
        
        if not pattern:
            logger.error(f"Kein Pattern für Feld '{field_name}' gefunden")
            return None
        
        try:
            match = re.search(pattern, text, re.IGNORECASE | re.MULTILINE)
            if match:
                value = match.group(1).strip()
                logger.info(f"Feld '{field_name}' extrahiert: '{value}'")
                return value
            else:
                logger.debug(f"Kein Match für Feld '{field_name}' gefunden")
                return None
                
        except re.error as e:
            logger.error(f"Regex-Fehler bei Feld '{field_name}': {e}")
            return None
        except Exception as e:
            logger.error(f"Unerwarteter Fehler bei Extraktion "
                         f"von '{field_name}': {e}")
            return None
    
    def extract_all_fields(self, text: str) -> Dict[str, str]:
        """
        Extrahiert alle konfigurierten Felder aus dem Text.
        
        Args:
            text: Zu durchsuchender Text
            
        Returns:
            Dictionary mit gefundenen Feld-Wert-Paaren
        """
        results = {}
        
        for field_name in self.patterns.keys():
            value = self.extract_field(text, field_name)
            if value:
                results[field_name] = value
        
        logger.info(f"Extraktion abgeschlossen: {len(results)} "
                    f"Felder gefunden")
        return results
    
    def validate_value(self, field_name: str, value: str) -> bool:
        """
        Validiert einen extrahierten Wert.
        
        Args:
            field_name: Name des Feldes
            value: Zu validierender Wert
            
        Returns:
            True wenn Wert gültig, False sonst
        """
        if field_name not in self.patterns:
            return False
        
        pattern_config = self.patterns[field_name]
        validation_pattern = pattern_config.get('validation')
        
        if not validation_pattern:
            # Keine Validierung definiert = immer gültig
            return True
        
        try:
            return bool(re.match(validation_pattern, value))
        except re.error as e:
            logger.error(f"Validierungs-Regex-Fehler für '{field_name}': {e}")
            return False
    
    def validate_iban(self, iban: str) -> bool:
        """
        Spezielle IBAN-Validierung mit Prüfsumme.
        
        Args:
            iban: Zu validierende IBAN
            
        Returns:
            True wenn IBAN gültig, False sonst
        """
        # Entferne Leerzeichen und konvertiere zu Großbuchstaben
        iban = iban.replace(' ', '').upper()
        
        # Prüfe Format
        if not re.match(r'^[A-Z]{2}\d{2}[A-Z0-9]{1,30}$', iban):
            return False
        
        # Prüfsummen-Validierung (vereinfacht)
        # Verschiebe erste 4 Zeichen ans Ende
        rearranged = iban[4:] + iban[:4]
        
        # Ersetze Buchstaben durch Zahlen (A=10, B=11, etc.)
        numeric = ''
        for char in rearranged:
            if char.isalpha():
                numeric += str(ord(char) - ord('A') + 10)
            else:
                numeric += char
        
        # Modulo 97 Test
        try:
            return int(numeric) % 97 == 1
        except ValueError:
            return False
    
    def get_pattern_info(self, field_name: str) -> Optional[Dict[str, Any]]:
        """
        Gibt Informationen über ein Pattern zurück.
        
        Args:
            field_name: Name des Feldes
            
        Returns:
            Pattern-Informationen oder None
        """
        return self.patterns.get(field_name)
    
    def get_all_patterns(self) -> Dict[str, Dict[str, Any]]:
        """Gibt alle verfügbaren Patterns zurück."""
        return self.patterns.copy()
    
    def test_pattern(self, field_name: str, test_text: str) -> Optional[str]:
        """
        Testet ein Pattern gegen einen Text.
        
        Args:
            field_name: Name des Feldes
            test_text: Test-Text
            
        Returns:
            Extrahierter Wert oder None
        """
        return self.extract_field(test_text, field_name)
    
    def reload_patterns(self) -> bool:
        """
        Lädt Patterns neu aus der Datei.
        
        Returns:
            True bei Erfolg, False bei Fehler
        """
        try:
            old_count = len(self.patterns)
            self.load_patterns()
            new_count = len(self.patterns)
            
            logger.info(f"Patterns neu geladen: {old_count} -> {new_count}")
            return True
            
        except Exception as e:
            logger.error(f"Fehler beim Neuladen der Patterns: {e}")
            return False

"""
Tests für das extractor-Modul.

Testet die Extraktion und Validierung von Dokumentfeldern.
"""

import pytest
import tempfile
import yaml
from pathlib import Path
import sys
import os

# Füge app-Verzeichnis zum Python-Path hinzu
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'app'))

from extractor import FieldExtractor


class TestFieldExtractor:
    """Tests für die FieldExtractor-Klasse."""
    
    @pytest.fixture
    def sample_patterns(self):
        """Beispiel-Patterns für Tests."""
        return {
            'rechnungsnummer': {
                'pattern': r'Rechnung(?:snummer)?:?\s*([A-Z0-9-]+)',
                'description': 'Test-Pattern für Rechnungsnummer',
                'validation': r'^[A-Z0-9-]+$'
            },
            'betrag': {
                'pattern': r'Betrag:?\s*(\d+[.,]\d{2})',
                'description': 'Test-Pattern für Betrag'
            }
        }
    
    @pytest.fixture
    def temp_pattern_file(self, sample_patterns):
        """Temporäre Pattern-Datei für Tests."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', 
                                       delete=False, encoding='utf-8') as f:
            yaml.dump(sample_patterns, f)
            temp_file = f.name
        
        yield temp_file
        
        # Cleanup
        Path(temp_file).unlink(missing_ok=True)
    
    def test_init_with_existing_file(self, temp_pattern_file):
        """Test Initialisierung mit existierender Pattern-Datei."""
        extractor = FieldExtractor(temp_pattern_file)
        assert len(extractor.patterns) == 2
        assert 'rechnungsnummer' in extractor.patterns
        assert 'betrag' in extractor.patterns
    
    def test_init_with_missing_file(self):
        """Test Initialisierung mit nicht-existierender Datei."""
        extractor = FieldExtractor('nonexistent.yaml')
        # Sollte Standard-Patterns laden
        assert len(extractor.patterns) > 0
        assert 'rechnungsnummer' in extractor.patterns
    
    def test_extract_rechnungsnummer(self, temp_pattern_file):
        """Test Extraktion von Rechnungsnummer."""
        extractor = FieldExtractor(temp_pattern_file)
        
        test_cases = [
            ("Rechnungsnummer: RG-2024-001", "RG-2024-001"),
            ("Rechnung RG123", "RG123"),
            ("Invoice Number: INV-456", None),  # Pattern passt nicht
            ("Keine Nummer hier", None)
        ]
        
        for text, expected in test_cases:
            result = extractor.extract_field(text, 'rechnungsnummer')
            assert result == expected
    
    def test_extract_betrag(self, temp_pattern_file):
        """Test Extraktion von Betrag."""
        extractor = FieldExtractor(temp_pattern_file)
        
        test_cases = [
            ("Betrag: 123,45", "123,45"),
            ("Betrag 999.99", "999.99"),
            ("Gesamtsumme: 1234,56", None),  # Pattern passt nicht
            ("Kein Betrag", None)
        ]
        
        for text, expected in test_cases:
            result = extractor.extract_field(text, 'betrag')
            assert result == expected
    
    def test_extract_all_fields(self, temp_pattern_file):
        """Test Extraktion aller Felder."""
        extractor = FieldExtractor(temp_pattern_file)
        
        text = """
        Rechnung: RG-2024-001
        Betrag: 199,99
        Weitere Informationen...
        """
        
        results = extractor.extract_all_fields(text)
        
        assert len(results) == 2
        assert results['rechnungsnummer'] == 'RG-2024-001'
        assert results['betrag'] == '199,99'
    
    def test_validate_value(self, temp_pattern_file):
        """Test Validierung von extrahierten Werten."""
        extractor = FieldExtractor(temp_pattern_file)
        
        # Test mit Validierung
        assert extractor.validate_value('rechnungsnummer', 'RG-123') == True
        assert extractor.validate_value('rechnungsnummer', 'invalid!') == False
        
        # Test ohne Validierung (betrag hat keine validation)
        assert extractor.validate_value('betrag', 'any_value') == True
        
        # Test mit unbekanntem Feld
        assert extractor.validate_value('unknown', 'value') == False
    
    def test_iban_validation(self, temp_pattern_file):
        """Test IBAN-Validierung."""
        extractor = FieldExtractor(temp_pattern_file)
        
        valid_ibans = [
            'DE89370400440532013000',  # Deutschland
            'GB29NWBK60161331926819',   # Großbritannien
            'FR1420041010050500013M02606'  # Frankreich
        ]
        
        invalid_ibans = [
            'DE89370400440532013001',  # Falsche Prüfsumme
            'XX123456789',             # Ungültiges Format
            'DE893704004405320130',    # Zu kurz
            'NOT_AN_IBAN'              # Kein IBAN-Format
        ]
        
        for iban in valid_ibans:
            assert extractor.validate_iban(iban) == True, f"IBAN {iban} sollte gültig sein"
        
        for iban in invalid_ibans:
            assert extractor.validate_iban(iban) == False, f"IBAN {iban} sollte ungültig sein"
    
    def test_pattern_reload(self, temp_pattern_file):
        """Test Neuladen von Patterns."""
        extractor = FieldExtractor(temp_pattern_file)
        initial_count = len(extractor.patterns)
        
        # Pattern-Datei modifizieren
        new_patterns = extractor.patterns.copy()
        new_patterns['new_field'] = {
            'pattern': r'New:?\s*(\w+)',
            'description': 'New test field'
        }
        
        with open(temp_pattern_file, 'w', encoding='utf-8') as f:
            yaml.dump(new_patterns, f)
        
        # Patterns neu laden
        success = extractor.reload_patterns()
        
        assert success == True
        assert len(extractor.patterns) == initial_count + 1
        assert 'new_field' in extractor.patterns
    
    def test_get_pattern_info(self, temp_pattern_file):
        """Test Abrufen von Pattern-Informationen."""
        extractor = FieldExtractor(temp_pattern_file)
        
        info = extractor.get_pattern_info('rechnungsnummer')
        assert info is not None
        assert 'pattern' in info
        assert 'description' in info
        
        # Unbekanntes Feld
        info = extractor.get_pattern_info('unknown_field')
        assert info is None
    
    def test_test_pattern(self, temp_pattern_file):
        """Test Pattern-Test-Funktion."""
        extractor = FieldExtractor(temp_pattern_file)
        
        result = extractor.test_pattern('rechnungsnummer', 'Rechnung: TEST-123')
        assert result == 'TEST-123'
        
        result = extractor.test_pattern('rechnungsnummer', 'Kein Match')
        assert result is None
        
        # Unbekanntes Feld
        result = extractor.test_pattern('unknown', 'Text')
        assert result is None


class TestComplexExtractions:
    """Tests für komplexere Extraktions-Szenarien."""
    
    def test_real_world_invoice_text(self):
        """Test mit realistischem Rechnungstext."""
        extractor = FieldExtractor()
        
        invoice_text = """
        RECHNUNG
        
        Rechnungsnummer: RG-2024-08-001
        Rechnungsdatum: 25.08.2024
        Kundennummer: K-12345
        
        Zahlbar bis: 24.09.2024
        
        Leistungsbeschreibung:
        - Dienstleistung A: 150,00 EUR
        - Dienstleistung B: 300,00 EUR
        
        Gesamtbetrag: 450,00 EUR
        
        Bankverbindung:
        IBAN: DE89370400440532013000
        BIC: COBADEFFXXX
        
        Kassenzeichen: KZ-2024-001
        """
        
        results = extractor.extract_all_fields(invoice_text)
        
        # Prüfe ob wichtige Felder extrahiert wurden
        assert 'rechnungsnummer' in results
        assert 'zahlungsziel' in results
        assert 'betrag' in results or 'gesamtbetrag' in results
        
        # Prüfe Werte
        assert results['rechnungsnummer'] == 'RG-2024-08-001'
        assert '24.09.2024' in results.get('zahlungsziel', '')
    
    def test_multiple_matches(self):
        """Test bei mehrfachen Matches (sollte ersten nehmen)."""
        extractor = FieldExtractor()
        
        text = """
        Erste Rechnung: RG-001
        Zweite Rechnung: RG-002
        """
        
        result = extractor.extract_field(text, 'rechnungsnummer')
        # Sollte ersten Match zurückgeben
        assert result == 'RG-001'


if __name__ == '__main__':
    pytest.main([__file__])

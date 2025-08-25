"""
Tests für die Konfiguration.

Testet das Laden und Validieren der Anwendungskonfiguration.
"""

import pytest
import tempfile
import os
from pathlib import Path
import sys

# Füge app-Verzeichnis zum Python-Path hinzu
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'app'))

from config import Config


class TestConfig:
    """Tests für die Config-Klasse."""
    
    def test_default_values(self):
        """Test Standard-Konfigurationswerte."""
        # Umgebungsvariablen temporär setzen
        os.environ['PAPERLESS_API_TOKEN'] = 'test_token'
        
        config = Config()
        
        assert config.paperless_api_url == 'http://localhost:8000'
        assert config.paperless_api_token == 'test_token'
        assert config.document_type == 'Rechnung'
        assert config.run_interval == 300
        assert config.web_port == 5000
        assert config.log_level == 'INFO'
        
        # Cleanup
        del os.environ['PAPERLESS_API_TOKEN']
    
    def test_env_file_loading(self):
        """Test Laden der Konfiguration aus .env-Datei."""
        # Temporäre .env-Datei erstellen
        with tempfile.NamedTemporaryFile(mode='w', suffix='.env', 
                                       delete=False, encoding='utf-8') as f:
            f.write("""
PAPERLESS_API_URL=http://test:8000
PAPERLESS_API_TOKEN=test_token_from_file
DOCUMENT_TYPE=Test Document
RUN_INTERVAL=600
WEB_PORT=3000
LOG_LEVEL=DEBUG
            """)
            env_file = f.name
        
        try:
            config = Config(env_file)
            
            assert config.paperless_api_url == 'http://test:8000'
            assert config.paperless_api_token == 'test_token_from_file'
            assert config.document_type == 'Test Document'
            assert config.run_interval == 600
            assert config.web_port == 3000
            assert config.log_level == 'DEBUG'
            
        finally:
            # Cleanup
            Path(env_file).unlink(missing_ok=True)
    
    def test_missing_api_token(self):
        """Test Fehler bei fehlendem API-Token."""
        # Sicherstellen dass Token nicht gesetzt ist
        if 'PAPERLESS_API_TOKEN' in os.environ:
            del os.environ['PAPERLESS_API_TOKEN']
        
        with pytest.raises(ValueError, match="PAPERLESS_API_TOKEN ist erforderlich"):
            Config()
    
    def test_boolean_conversion(self):
        """Test Konvertierung von Boolean-Werten."""
        os.environ['PAPERLESS_API_TOKEN'] = 'test'
        os.environ['VALIDATE_EXTRACTED_VALUES'] = 'false'
        os.environ['SKIP_PROCESSED_DOCUMENTS'] = 'true'
        
        config = Config()
        
        assert config.validate_extracted_values == False
        assert config.skip_processed_documents == True
        
        # Cleanup
        del os.environ['PAPERLESS_API_TOKEN']
        del os.environ['VALIDATE_EXTRACTED_VALUES']
        del os.environ['SKIP_PROCESSED_DOCUMENTS']
    
    def test_integer_conversion(self):
        """Test Konvertierung von Integer-Werten."""
        os.environ['PAPERLESS_API_TOKEN'] = 'test'
        os.environ['RUN_INTERVAL'] = '123'
        os.environ['WEB_PORT'] = '8080'
        os.environ['LOG_BACKUP_COUNT'] = '7'
        
        config = Config()
        
        assert config.run_interval == 123
        assert config.web_port == 8080
        assert config.log_backup_count == 7
        
        # Cleanup
        del os.environ['PAPERLESS_API_TOKEN']
        del os.environ['RUN_INTERVAL']
        del os.environ['WEB_PORT']
        del os.environ['LOG_BACKUP_COUNT']
    
    def test_get_config_dict(self):
        """Test Abrufen der Konfiguration als Dictionary."""
        os.environ['PAPERLESS_API_TOKEN'] = 'test'
        
        config = Config()
        config_dict = config.get_config_dict()
        
        assert isinstance(config_dict, dict)
        assert 'paperless_api_url' in config_dict
        assert 'paperless_api_token' not in config_dict  # Sollte aus Sicherheitsgründen nicht enthalten sein
        assert 'document_type' in config_dict
        
        # Cleanup
        del os.environ['PAPERLESS_API_TOKEN']


if __name__ == '__main__':
    pytest.main([__file__])

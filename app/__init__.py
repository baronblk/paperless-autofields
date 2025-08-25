"""
Paperless AutoFields - Automatische Felderkennung für Paperless-NGX

Dieses Package enthält alle Module für die automatische Extraktion und
Befüllung von Custom Fields in Paperless-NGX Dokumenten.

Hauptmodule:
- config: Konfigurationsmanagement
- api: Paperless-NGX API Integration 
- extractor: OCR/Regex Feldextraktion
- autofill: Hauptverarbeitungslogik
- cli: Kommandozeilen-Interface
- webui: Web-Interface (Flask)
"""

__version__ = "1.0.0"
__author__ = "baronblk"
__description__ = "Paperless-NGX AutoFields - Automatische Felderkennung"

# Hauptklassen für einfachen Import
from .config import Config
from .api import PaperlessAPI
from .extractor import FieldExtractor
from .autofill import AutoFieldProcessor

__all__ = [
    'Config',
    'PaperlessAPI',
    'FieldExtractor',
    'AutoFieldProcessor'
]

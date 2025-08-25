"""
Pytest Konfiguration für Tests.

Stellt sicher, dass das app-Modul importiert werden kann.
"""

import sys
import os

# Füge das Hauptverzeichnis zum Python-Path hinzu
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

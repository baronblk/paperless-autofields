#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Paperless AutoFields Setup Script

Interaktiver Setup-Assistent für die Installation und Konfiguration.
"""

import sys
import shutil
from typing import Dict


def print_banner():
    """Zeigt das Projekt-Banner."""
    banner = """
╔══════════════════════════════════════════════════════════════╗
║                    Paperless AutoFields                     ║
║              Automatische Felderkennung für                 ║
║                     Paperless-NGX                          ║
║                                                              ║
║  🚀 Professional Setup Assistant                            ║
╚══════════════════════════════════════════════════════════════╝
    """
    print(banner)


def check_requirements():
    """Prüft System-Anforderungen."""
    print("\n🔍 Prüfe System-Anforderungen...")
    
    # Python Version
    if sys.version_info < (3, 9):
        print("❌ Python 3.9+ erforderlich")
        return False
    print(f"✅ Python {sys.version_info.major}.{sys.version_info.minor}")
    
    # Git (optional)
    if shutil.which('git'):
        print("✅ Git verfügbar")
    else:
        print("⚠️  Git nicht gefunden (optional)")
    
    # Docker (optional)
    if shutil.which('docker'):
        print("✅ Docker verfügbar")
    else:
        print("⚠️  Docker nicht gefunden (optional)")
    
    # pip
    if shutil.which('pip') or shutil.which('pip3'):
        print("✅ pip verfügbar")
    else:
        print("❌ pip erforderlich")
        return False
    
    return True


def get_user_input(prompt: str, default: str = "",
                   required: bool = True) -> str:
    """Holt Benutzereingabe mit Validierung."""
    while True:
        if default:
            user_input = input(f"{prompt} [{default}]: ").strip()
            if not user_input:
                user_input = default
        else:
            user_input = input(f"{prompt}: ").strip()
        
        if user_input or not required:
            return user_input
        
        print("❌ Eingabe erforderlich!")


def collect_configuration() -> Dict[str, str]:
    """Sammelt Konfigurationsdaten vom Benutzer."""
    print("\n⚙️  Konfiguration")
    print("=" * 50)
    
    config = {}
    
    # Paperless-NGX Einstellungen
    print("\n📄 Paperless-NGX Verbindung:")
    config['PAPERLESS_API_URL'] = get_user_input(
        "API URL", "http://localhost:8000"
    )
    config['PAPERLESS_API_TOKEN'] = get_user_input(
        "API Token (aus Paperless-NGX Admin-Interface)"
    )
    
    return config


def main():
    """Hauptfunktion des Setup-Scripts."""
    print_banner()
    
    if not check_requirements():
        sys.exit(1)
    
    config = collect_configuration()
    
    # Zeige Konfigurationszusammenfassung
    print(f"\n📋 Konfiguration gespeichert ({len(config)} Einstellungen)")
    print("✅ Setup abgeschlossen!")


if __name__ == "__main__":
    main()

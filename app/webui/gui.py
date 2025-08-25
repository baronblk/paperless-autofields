"""
Paperless AutoFields - Web GUI

Flask-basierte Benutzeroberfläche zur Konfiguration und Überwachung.
"""

import os
import sys
import yaml
import json
from pathlib import Path
from flask import Flask, render_template, request, jsonify, redirect, url_for
from loguru import logger

# Füge app-Verzeichnis zum Python-Path hinzu
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from config import Config
from api import PaperlessAPI
from extractor import FieldExtractor


app = Flask(__name__)
app.secret_key = os.environ.get('SECRET_KEY', 'dev-key-change-in-production')

# Globale Variablen
config = None
api = None
extractor = None


def init_app():
    """Initialisiert die Anwendungskomponenten."""
    global config, api, extractor
    
    try:
        config = Config()
        api = PaperlessAPI(config.paperless_api_url, config.paperless_api_token)
        extractor = FieldExtractor(config.pattern_file)
        logger.success("Web-GUI erfolgreich initialisiert")
    except Exception as e:
        logger.error(f"Fehler bei GUI-Initialisierung: {e}")
        return False
    return True


@app.route('/')
def index():
    """Hauptseite mit Dashboard."""
    if not init_app():
        return render_template('error.html', 
                             error="Initialisierungsfehler"), 500
    
    try:
        # Statistiken sammeln
        documents = api.get_documents_by_type(config.document_type)
        custom_fields = api.get_custom_fields()
        patterns = extractor.get_all_patterns()
        
        stats = {
            'total_documents': len(documents),
            'custom_fields': len(custom_fields),
            'patterns': len(patterns),
            'document_type': config.document_type
        }
        
        return render_template('dashboard.html', stats=stats)
        
    except Exception as e:
        logger.error(f"Dashboard-Fehler: {e}")
        return render_template('error.html', error=str(e)), 500


@app.route('/config')
def config_page():
    """Konfigurationsseite."""
    if not config:
        init_app()
    
    return render_template('config.html', config=config.get_config_dict())


@app.route('/patterns')
def patterns_page():
    """Pattern-Verwaltungsseite."""
    if not extractor:
        init_app()
    
    patterns = extractor.get_all_patterns()
    return render_template('patterns.html', patterns=patterns)


@app.route('/api/patterns', methods=['GET'])
def api_get_patterns():
    """API: Alle Patterns abrufen."""
    if not extractor:
        init_app()
    
    return jsonify(extractor.get_all_patterns())


@app.route('/api/patterns/<field_name>', methods=['PUT'])
def api_update_pattern(field_name):
    """API: Pattern aktualisieren."""
    if not extractor:
        return jsonify({'error': 'Extractor nicht initialisiert'}), 500
    
    try:
        data = request.get_json()
        
        # Pattern-Datei laden
        pattern_file = Path(config.pattern_file)
        if pattern_file.exists():
            with open(pattern_file, 'r', encoding='utf-8') as f:
                patterns = yaml.safe_load(f) or {}
        else:
            patterns = {}
        
        # Pattern aktualisieren
        patterns[field_name] = data
        
        # Datei speichern
        with open(pattern_file, 'w', encoding='utf-8') as f:
            yaml.dump(patterns, f, default_flow_style=False, 
                     allow_unicode=True, indent=2)
        
        # Patterns neu laden
        extractor.reload_patterns()
        
        return jsonify({'success': True, 'message': 'Pattern aktualisiert'})
        
    except Exception as e:
        logger.error(f"Fehler beim Aktualisieren des Patterns: {e}")
        return jsonify({'error': str(e)}), 500


@app.route('/api/test-pattern', methods=['POST'])
def api_test_pattern():
    """API: Pattern gegen Text testen."""
    if not extractor:
        return jsonify({'error': 'Extractor nicht initialisiert'}), 500
    
    try:
        data = request.get_json()
        field_name = data.get('field_name')
        test_text = data.get('test_text')
        
        if not field_name or not test_text:
            return jsonify({'error': 'field_name und test_text erforderlich'}), 400
        
        result = extractor.test_pattern(field_name, test_text)
        
        return jsonify({
            'field_name': field_name,
            'result': result,
            'found': result is not None
        })
        
    except Exception as e:
        logger.error(f"Fehler beim Testen des Patterns: {e}")
        return jsonify({'error': str(e)}), 500


@app.route('/api/documents')
def api_documents():
    """API: Dokumente abrufen."""
    if not api:
        return jsonify({'error': 'API nicht initialisiert'}), 500
    
    try:
        documents = api.get_documents_by_type(config.document_type)
        return jsonify(documents)
    except Exception as e:
        logger.error(f"Fehler beim Abrufen der Dokumente: {e}")
        return jsonify({'error': str(e)}), 500


@app.route('/api/process-document/<int:document_id>', methods=['POST'])
def api_process_document(document_id):
    """API: Einzelnes Dokument verarbeiten."""
    if not api or not extractor:
        return jsonify({'error': 'Komponenten nicht initialisiert'}), 500
    
    try:
        # Dokument-Daten abrufen
        documents = api.get_documents_by_type(config.document_type)
        document = next((d for d in documents if d['id'] == document_id), None)
        
        if not document:
            return jsonify({'error': 'Dokument nicht gefunden'}), 404
        
        # OCR-Inhalt abrufen
        content = api.get_document_content(document_id)
        if not content:
            return jsonify({'error': 'Kein OCR-Inhalt verfügbar'}), 400
        
        # Felder extrahieren
        extracted_fields = extractor.extract_all_fields(content)
        
        # Ergebnis zurückgeben
        return jsonify({
            'document_id': document_id,
            'extracted_fields': extracted_fields,
            'success': True
        })
        
    except Exception as e:
        logger.error(f"Fehler bei Dokumentverarbeitung: {e}")
        return jsonify({'error': str(e)}), 500


@app.route('/logs')
def logs_page():
    """Log-Anzeige-Seite."""
    try:
        log_file = Path(config.log_file) if config else Path('logs/paperless-autofields.log')
        
        if log_file.exists():
            with open(log_file, 'r', encoding='utf-8') as f:
                # Lese die letzten 100 Zeilen
                lines = f.readlines()
                recent_logs = lines[-100:] if len(lines) > 100 else lines
        else:
            recent_logs = ["Log-Datei nicht gefunden"]
        
        return render_template('logs.html', logs=recent_logs)
        
    except Exception as e:
        logger.error(f"Fehler beim Laden der Logs: {e}")
        return render_template('error.html', error=str(e)), 500


@app.route('/health')
def health_check():
    """Health Check Endpoint."""
    try:
        if not config:
            init_app()
        
        status = {
            'status': 'healthy',
            'api_connected': api is not None,
            'patterns_loaded': extractor is not None and len(extractor.get_all_patterns()) > 0,
            'timestamp': __import__('datetime').datetime.now().isoformat()
        }
        
        return jsonify(status)
        
    except Exception as e:
        return jsonify({
            'status': 'unhealthy',
            'error': str(e),
            'timestamp': __import__('datetime').datetime.now().isoformat()
        }), 500


def create_templates():
    """Erstellt Template-Verzeichnis und Basis-Templates."""
    templates_dir = Path(__file__).parent / 'templates'
    templates_dir.mkdir(exist_ok=True)
    
    # Basis-Template
    base_template = '''<!DOCTYPE html>
<html lang="de">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Paperless AutoFields</title>
    <style>
        body { font-family: Arial, sans-serif; margin: 0; padding: 20px; }
        .container { max-width: 1200px; margin: 0 auto; }
        .nav { background: #333; color: white; padding: 10px; margin-bottom: 20px; }
        .nav a { color: white; text-decoration: none; margin-right: 15px; }
        .nav a:hover { text-decoration: underline; }
        .card { border: 1px solid #ddd; padding: 15px; margin-bottom: 15px; }
        .error { color: red; background: #ffe6e6; padding: 10px; }
        .success { color: green; background: #e6ffe6; padding: 10px; }
    </style>
</head>
<body>
    <div class="nav">
        <a href="/">Dashboard</a>
        <a href="/patterns">Patterns</a>
        <a href="/config">Konfiguration</a>
        <a href="/logs">Logs</a>
        <a href="/health">Health</a>
    </div>
    <div class="container">
        {% block content %}{% endblock %}
    </div>
</body>
</html>'''
    
    with open(templates_dir / 'base.html', 'w', encoding='utf-8') as f:
        f.write(base_template)
    
    # Dashboard-Template
    dashboard_template = '''{% extends "base.html" %}
{% block content %}
<h1>Paperless AutoFields Dashboard</h1>
<div class="card">
    <h2>Statistiken</h2>
    <p><strong>Dokumenttyp:</strong> {{ stats.document_type }}</p>
    <p><strong>Dokumente gefunden:</strong> {{ stats.total_documents }}</p>
    <p><strong>Custom Fields:</strong> {{ stats.custom_fields }}</p>
    <p><strong>Patterns konfiguriert:</strong> {{ stats.patterns }}</p>
</div>
{% endblock %}'''
    
    with open(templates_dir / 'dashboard.html', 'w', encoding='utf-8') as f:
        f.write(dashboard_template)
    
    # Weitere Templates...
    error_template = '''{% extends "base.html" %}
{% block content %}
<h1>Fehler</h1>
<div class="error">{{ error }}</div>
{% endblock %}'''
    
    with open(templates_dir / 'error.html', 'w', encoding='utf-8') as f:
        f.write(error_template)


def main():
    """Startet die Web-GUI."""
    # Templates erstellen falls nicht vorhanden
    create_templates()
    
    # Konfiguration laden
    if not init_app():
        logger.error("GUI konnte nicht initialisiert werden")
        sys.exit(1)
    
    # Server starten
    logger.info(f"Starte Web-GUI auf {config.web_host}:{config.web_port}")
    app.run(
        host=config.web_host,
        port=config.web_port,
        debug=False
    )


if __name__ == "__main__":
    main()

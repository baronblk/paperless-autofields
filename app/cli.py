"""
Paperless AutoFields - Command Line Interface

CLI-Tool für manuelle Feldinjektionen und Verwaltungsaufgaben.
"""

import argparse
import sys
import json
from loguru import logger
from .config import Config
from .api import PaperlessAPI
from .extractor import FieldExtractor


def setup_cli_logging():
    """Konfiguriert das Logging für CLI-Nutzung."""
    logger.remove()
    logger.add(
        sys.stdout,
        level="INFO",
        format=("<green>{time:HH:mm:ss}</green> | <level>{level}</level> | "
                "{message}"),
        colorize=True
    )


def cmd_set_field(args):
    """Setzt ein Custom Field für ein Dokument."""
    config = Config()
    api = PaperlessAPI(config.paperless_api_url, config.paperless_api_token)
    
    success = api.set_custom_field_value(
        args.document_id, args.field, args.value)
    
    if success:
        logger.success(f"Feld '{args.field}' für Dokument {args.document_id} "
                       f"auf '{args.value}' gesetzt")
        return 0
    else:
        logger.error("Fehler beim Setzen des Feldes")
        return 1


def cmd_extract_fields(args):
    """Extrahiert Felder aus einem Dokument."""
    config = Config()
    api = PaperlessAPI(config.paperless_api_url, config.paperless_api_token)
    extractor = FieldExtractor(config.pattern_file)
    
    # OCR-Inhalt abrufen
    content = api.get_document_content(args.document_id)
    if not content:
        logger.error(f"Kein Inhalt für Dokument {args.document_id} gefunden")
        return 1
    
    # Felder extrahieren
    if args.field:
        # Einzelnes Feld
        value = extractor.extract_field(content, args.field)
        if value:
            result = {args.field: value}
        else:
            result = {}
    else:
        # Alle Felder
        result = extractor.extract_all_fields(content)
    
    # Ausgabe
    if args.json:
        print(json.dumps(result, indent=2, ensure_ascii=False))
    else:
        if result:
            logger.info(f"Extrahierte Felder für Dokument {args.document_id}:")
            for field, value in result.items():
                print(f"  {field}: {value}")
        else:
            logger.warning("Keine Felder gefunden")
    
    return 0


def cmd_list_documents(args):
    """Listet Dokumente auf."""
    config = Config()
    api = PaperlessAPI(config.paperless_api_url, config.paperless_api_token)
    
    doc_type = args.document_type or config.document_type
    documents = api.get_documents_by_type(doc_type)
    
    if args.json:
        print(json.dumps(documents, indent=2, ensure_ascii=False))
    else:
        logger.info(f"Gefunden: {len(documents)} Dokumente")
        for doc in documents[:args.limit]:
            title = doc.get('title', 'Unbekannt')[:50]
            created = doc.get('created', 'Unbekannt')[:10]
            print(f"  {doc['id']:>6} | {created} | {title}")
    
    return 0


def cmd_test_pattern(args):
    """Testet ein Pattern gegen Text."""
    config = Config()
    extractor = FieldExtractor(config.pattern_file)
    
    # Text aus Datei oder Kommandozeile
    if args.file:
        with open(args.file, 'r', encoding='utf-8') as f:
            text = f.read()
    else:
        text = args.text
    
    if not text:
        logger.error("Kein Text zum Testen angegeben")
        return 1
    
    # Pattern testen
    result = extractor.test_pattern(args.field, text)
    
    if args.json:
        print(json.dumps({
            'field': args.field,
            'result': result,
            'found': result is not None
        }, indent=2, ensure_ascii=False))
    else:
        if result:
            logger.success(f"Pattern '{args.field}' gefunden: '{result}'")
        else:
            logger.warning(f"Pattern '{args.field}' nicht gefunden")
    
    return 0 if result else 1


def cmd_process_document(args):
    """Verarbeitet ein einzelnes Dokument."""
    config = Config()
    api = PaperlessAPI(config.paperless_api_url, config.paperless_api_token)
    extractor = FieldExtractor(config.pattern_file)
    
    # Dokument-Daten abrufen
    documents = api.get_documents_by_type(config.document_type)
    # Dokument suchen
    document = next((d for d in documents if d['id'] == args.document_id),
                    None)
    
    if not document:
        logger.error(f"Dokument {args.document_id} nicht gefunden")
        return 1
    
    logger.info(f"Verarbeite Dokument {args.document_id}: {document.get('title', 'Unbekannt')}")
    
    # OCR-Inhalt abrufen
    content = api.get_document_content(args.document_id)
    if not content:
        logger.error("Kein OCR-Inhalt verfügbar")
        return 1
    
    # Felder extrahieren
    extracted_fields = extractor.extract_all_fields(content)
    
    if not extracted_fields:
        logger.info("Keine Felder extrahiert")
        return 0
    
    # Felder setzen (falls nicht dry-run)
    if args.dry_run:
        logger.info("Dry-run Modus - Felder werden nicht gesetzt:")
        for field, value in extracted_fields.items():
            print(f"  {field}: {value}")
    else:
        success_count = 0
        for field, value in extracted_fields.items():
            if api.set_custom_field_value(args.document_id, field, value):
                success_count += 1
                logger.success(f"  {field}: {value}")
            else:
                logger.error(f"  Fehler bei {field}: {value}")
        
        logger.info(f"{success_count}/{len(extracted_fields)} Felder erfolgreich gesetzt")
    
    return 0


def cmd_list_patterns(args):
    """Listet verfügbare Patterns auf."""
    config = Config()
    extractor = FieldExtractor(config.pattern_file)
    
    patterns = extractor.get_all_patterns()
    
    if args.json:
        print(json.dumps(patterns, indent=2, ensure_ascii=False))
    else:
        logger.info(f"Verfügbare Patterns ({len(patterns)}):")
        for name, info in patterns.items():
            description = info.get('description', 'Keine Beschreibung')
            print(f"  {name:20} | {description}")
    
    return 0


def main():
    """Haupteinstiegspunkt des CLI."""
    setup_cli_logging()
    
    parser = argparse.ArgumentParser(
        description="Paperless AutoFields CLI",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Beispiele:
  %(prog)s set-field 123 rechnungsnummer "RG-2024-001"
  %(prog)s extract 123 --field rechnungsnummer
  %(prog)s extract 123 --json
  %(prog)s list-docs --limit 10
  %(prog)s test-pattern rechnungsnummer --text "Rechnung: RG-123"
  %(prog)s process 123 --dry-run
        """
    )
    
    parser.add_argument('--json', action='store_true',
                       help='Ausgabe im JSON-Format')
    
    subparsers = parser.add_subparsers(dest='command', help='Verfügbare Kommandos')
    
    # set-field Kommando
    parser_set = subparsers.add_parser('set-field',
                                      help='Setzt ein Custom Field für ein Dokument')
    parser_set.add_argument('document_id', type=int, help='Dokument-ID')
    parser_set.add_argument('field', help='Feldname')
    parser_set.add_argument('value', help='Feldwert')
    
    # extract Kommando
    parser_extract = subparsers.add_parser('extract',
                                          help='Extrahiert Felder aus einem Dokument')
    parser_extract.add_argument('document_id', type=int, help='Dokument-ID')
    parser_extract.add_argument('--field', help='Spezifisches Feld (optional)')
    
    # list-docs Kommando
    parser_list = subparsers.add_parser('list-docs',
                                       help='Listet Dokumente auf')
    parser_list.add_argument('--document-type', help='Dokumenttyp (optional)')
    parser_list.add_argument('--limit', type=int, default=50,
                            help='Maximale Anzahl Dokumente (default: 50)')
    
    # test-pattern Kommando
    parser_test = subparsers.add_parser('test-pattern',
                                       help='Testet ein Pattern gegen Text')
    parser_test.add_argument('field', help='Pattern-Name')
    parser_test.add_argument('--text', help='Test-Text')
    parser_test.add_argument('--file', help='Text-Datei')
    
    # process Kommando
    parser_process = subparsers.add_parser('process',
                                          help='Verarbeitet ein Dokument')
    parser_process.add_argument('document_id', type=int, help='Dokument-ID')
    parser_process.add_argument('--dry-run', action='store_true',
                               help='Zeigt nur was gesetzt würde')
    
    # list-patterns Kommando
    parser_patterns = subparsers.add_parser('list-patterns',
                                           help='Listet verfügbare Patterns auf')
    
    args = parser.parse_args()
    
    if not args.command:
        parser.print_help()
        return 1
    
    # Kommando ausführen
    try:
        if args.command == 'set-field':
            return cmd_set_field(args)
        elif args.command == 'extract':
            return cmd_extract_fields(args)
        elif args.command == 'list-docs':
            return cmd_list_documents(args)
        elif args.command == 'test-pattern':
            return cmd_test_pattern(args)
        elif args.command == 'process':
            return cmd_process_document(args)
        elif args.command == 'list-patterns':
            return cmd_list_patterns(args)
        else:
            logger.error(f"Unbekanntes Kommando: {args.command}")
            return 1
            
    except KeyboardInterrupt:
        logger.info("Unterbrochen durch Benutzer")
        return 1
    except Exception as e:
        logger.error(f"Fehler: {e}")
        return 1


if __name__ == "__main__":
    sys.exit(main())

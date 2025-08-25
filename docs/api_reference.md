# Paperless‑NGX REST API Referenz

##  Authentifizierung

Für alle API-Aufrufe musst du im HTTP-Header folgendes mitsenden:


Außerdem unterstützt Paperless-NGX (ab Version 1.3.0) API-Versionierung:
```http
Accept: application/json; version=6

Und bestätigt im Response-Header mit X-Api-Version und X-Version

API-Endpunkte & CRUD-Funktionalität

Die API basiert auf Django REST Framework und bietet für folgende Ressourcen Full CRUD (sofern nicht anders angegeben): 
Gitea Labexposed

correspondents

custom_fields

documents (CRUD; POST für Upload siehe unten)

document_types

groups

mail_accounts

mail_rules

profile (GET, PATCH)

share_links

storage_paths

tags

users

workflows

logs (nur Lesenderzugriff)

tasks (read-only)

Alle Endpunkte sind auch per {id} adressierbar, z. B. /api/documents/454/.

Dokumente (documents)

GET /api/documents/ (Filter z. B. document_type=, correspondent=, etc.)

GET /api/documents/{id}/

liefert u. a. Felder wie id, title, content, tags, document_type, correspondent, created, added, archive_serial_number, notes, custom_fields 
Paperless NGX Dokumentation
+4
Wikipedia
+4
Paperless NGX Dokumentation
+4
Paperless NGX Dokumentation
+7
Gitea Labexposed
+7
Glama – MCP Hosting Platform
+7

Zusatzendpunkte:

/api/documents/{id}/download/

/api/documents/{id}/preview/

/api/documents/{id}/thumb/

/api/documents/{id}/metadata/ mit PDF- und Dateiinformationen 
Gitea Labexposed

Dokumententypen (document_types)

GET /api/document_types/
Liefert Liste mit {id, name, slug} 
Gitea Labexposed
+1
PyPI
+1

Benutzerdefinierte Felder (custom_fields)

GET /api/custom_fields/

POST /api/custom_field_values/ mit Payload:

{
  "document": 123,
  "custom_field": 4,
  "value": "47110815"
}


Hinweis: Jeder POST erzeugt einen neuen Eintrag – es gibt kein Update eines bestehenden Werts 
Gitea Labexposed
Wikipedia
.

Dokument Upload /api/documents/post_document/

Form-Daten-Payload (multipart):

document: Datei

optional: title, created, correspondent, document_type, storage_path, tags, archive_serial_number, custom_fields

Antwort: UUID des task zur Überwachung via /api/tasks/?task_id=... 
Paperless NGX Dokumentation
+4
Gitea Labexposed
+4
Glama – MCP Hosting Platform
+4

Bulk-Operationen (documents/bulk_edit/)

POST-Payload-Beispiel:

{
  "documents": [1,2,3],
  "method": "add_tag",
  "parameters": { "tag": TAG_ID }
}


Unterstützte Methoden:

set_correspondent

set_document_type

set_storage_path

add_tag / remove_tag / modify_tags

delete

redo_ocr

set_permissions

merge

split

Permission-Parameter erlauben granular individuelle Rechtevergabe 
Gitea Labexposed
+1
Paperless NGX Dokumentation
+1

Suche & Autocomplete

Fulltext-Suche: /api/documents/?query=suche

Ähnliche Dokumente: /api/documents/?more_like_id=1234
(Mit Rückgabe von Score, Highlights etc.) 
Glama – MCP Hosting Platform
+10
Gitea Labexposed
+10
Paperless NGX Dokumentation
+10

Autocomplete: /api/search/autocomplete/?term=...&limit=10 liefert ein Array von Vorschlägen 
Gitea Labexposed

Erlaubnissteuerung (permissions)

Alle Objekte unterstützen optionale Felder owner, set_permissions mit Struktur für view/change (Users & Groups). full_perms=true erlaubt Abfrage vollständiger Rechte 
Gitea Labexposed

Zusammenfassung
Feature	Endpunkt
Dokumente	/api/documents/
Document Types	/api/document_types/
Custom Fields	/api/custom_fields/, /custom_field_values/
Upload Dokument	/api/documents/post_document/
Suche	/api/documents/?query=...
Bulk Operationen	/api/documents/bulk_edit/
Autocomplete	/api/search/autocomplete/
Rechteverwaltung	Verschiedene Endpunkte mit set_permissions
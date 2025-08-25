"""
Paperless AutoFields - API Communication

Dieses Modul verwaltet die REST-Kommunikation mit der Paperless-NGX API.
"""

import requests
from typing import List, Dict, Optional, Any
from loguru import logger


class PaperlessAPI:
    """API-Client für Paperless-NGX."""
    
    def __init__(self, api_url: str, api_token: str):
        """
        Initialisiert den API-Client.
        
        Args:
            api_url: Basis-URL der Paperless-NGX API
            api_token: API-Token für Authentifizierung
        """
        self.api_url = api_url.rstrip('/')
        self.headers = {
            'Authorization': f'Token {api_token}',
            'Content-Type': 'application/json'
        }
        self.session = requests.Session()
        self.session.headers.update(self.headers)
        
        # Test der API-Verbindung
        self._test_connection()
    
    def _test_connection(self) -> None:
        """Testet die Verbindung zur API."""
        try:
            response = self.session.get(f'{self.api_url}/api/documents/',
                                      params={'page_size': 1})
            response.raise_for_status()
            logger.success("Verbindung zur Paperless-NGX API erfolgreich")
        except requests.exceptions.RequestException as e:
            logger.error(f"Fehler beim Verbinden zur API: {e}")
            raise
    
    def get_documents_by_type(self, document_type: str,
                            page_size: int = 100) -> List[Dict[str, Any]]:
        """
        Ruft alle Dokumente eines bestimmten Typs ab.
        
        Args:
            document_type: Name des Dokumenttyps
            page_size: Anzahl Dokumente pro Seite
            
        Returns:
            Liste aller Dokumente des angegebenen Typs
        """
        documents = []
        page = 1
        
        while True:
            try:
                response = self.session.get(
                    f'{self.api_url}/api/documents/',
                    params={
                        'document_type__name': document_type,
                        'page': page,
                        'page_size': page_size
                    }
                )
                response.raise_for_status()
                data = response.json()
                
                documents.extend(data['results'])
                
                if not data['next']:
                    break
                    
                page += 1
                
            except requests.exceptions.RequestException as e:
                logger.error(f"Fehler beim Abrufen der Dokumente: {e}")
                break
        
        logger.info(f"Gefunden: {len(documents)} Dokumente vom Typ "
                   f"'{document_type}'")
        return documents
    
    def get_document_content(self, document_id: int) -> Optional[str]:
        """
        Ruft den OCR-Inhalt eines Dokuments ab.
        
        Args:
            document_id: ID des Dokuments
            
        Returns:
            OCR-Text des Dokuments oder None bei Fehler
        """
        try:
            response = self.session.get(
                f'{self.api_url}/api/documents/{document_id}/'
            )
            response.raise_for_status()
            document_data = response.json()
            
            return document_data.get('content', '')
            
        except requests.exceptions.RequestException as e:
            logger.error(f"Fehler beim Abrufen des Dokumentinhalts "
                        f"für ID {document_id}: {e}")
            return None
    
    def get_custom_fields(self) -> List[Dict[str, Any]]:
        """
        Ruft alle verfügbaren Custom Fields ab.
        
        Returns:
            Liste aller Custom Fields
        """
        try:
            response = self.session.get(f'{self.api_url}/api/custom_fields/')
            response.raise_for_status()
            data = response.json()
            
            fields = data.get('results', [])
            logger.info(f"Gefunden: {len(fields)} Custom Fields")
            return fields
            
        except requests.exceptions.RequestException as e:
            logger.error(f"Fehler beim Abrufen der Custom Fields: {e}")
            return []
    
    def get_custom_field_by_name(self, field_name: str) -> Optional[Dict]:
        """
        Sucht ein Custom Field anhand des Namens.
        
        Args:
            field_name: Name des Custom Fields
            
        Returns:
            Custom Field-Daten oder None falls nicht gefunden
        """
        fields = self.get_custom_fields()
        for field in fields:
            if field.get('name') == field_name:
                return field
        
        logger.warning(f"Custom Field '{field_name}' nicht gefunden")
        return None
    
    def set_custom_field_value(self, document_id: int, field_name: str,
                              value: str) -> bool:
        """
        Setzt den Wert eines Custom Fields für ein Dokument.
        
        Args:
            document_id: ID des Dokuments
            field_name: Name des Custom Fields
            value: Zu setzender Wert
            
        Returns:
            True bei Erfolg, False bei Fehler
        """
        # Erst Custom Field ID ermitteln
        field = self.get_custom_field_by_name(field_name)
        if not field:
            logger.error(f"Custom Field '{field_name}' existiert nicht")
            return False
        
        field_id = field['id']
        
        try:
            # Prüfen ob bereits ein Wert gesetzt ist
            response = self.session.get(
                f'{self.api_url}/api/custom_field_instances/',
                params={
                    'document': document_id,
                    'field': field_id
                }
            )
            response.raise_for_status()
            instances = response.json().get('results', [])
            
            if instances:
                # Wert aktualisieren
                instance_id = instances[0]['id']
                response = self.session.patch(
                    f'{self.api_url}/api/custom_field_instances/{instance_id}/',
                    json={'value': value}
                )
            else:
                # Neuen Wert erstellen
                response = self.session.post(
                    f'{self.api_url}/api/custom_field_instances/',
                    json={
                        'document': document_id,
                        'field': field_id,
                        'value': value
                    }
                )
            
            response.raise_for_status()
            logger.success(f"Custom Field '{field_name}' für Dokument "
                          f"{document_id} auf '{value}' gesetzt")
            return True
            
        except requests.exceptions.RequestException as e:
            logger.error(f"Fehler beim Setzen des Custom Fields: {e}")
            return False
    
    def get_document_custom_fields(self, document_id: int) -> Dict[str, str]:
        """
        Ruft alle Custom Field-Werte eines Dokuments ab.
        
        Args:
            document_id: ID des Dokuments
            
        Returns:
            Dictionary mit Field-Namen als Keys und Werten als Values
        """
        try:
            response = self.session.get(
                f'{self.api_url}/api/custom_field_instances/',
                params={'document': document_id}
            )
            response.raise_for_status()
            instances = response.json().get('results', [])
            
            # Field IDs zu Namen auflösen
            fields = {f['id']: f['name'] for f in self.get_custom_fields()}
            
            result = {}
            for instance in instances:
                field_id = instance['field']
                field_name = fields.get(field_id, f'Unknown_{field_id}')
                result[field_name] = instance['value']
            
            return result
            
        except requests.exceptions.RequestException as e:
            logger.error(f"Fehler beim Abrufen der Custom Fields "
                        f"für Dokument {document_id}: {e}")
            return {}

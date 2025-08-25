#!/bin/bash

# Paperless AutoFields Health Monitor
# Überwacht die Anwendung und startet Services bei Bedarf neu

APP_NAME="paperless-autofields"
LOG_FILE="/var/log/${APP_NAME}/health-monitor.log"
HEALTH_URL="http://localhost:5000/health"
MAX_RETRIES=3
RETRY_DELAY=10

# Logging
log() {
    echo "$(date '+%Y-%m-%d %H:%M:%S') - $1" | tee -a "${LOG_FILE}"
}

# Prüfe Service Status
check_service() {
    local service_name="$1"
    
    if systemctl is-active --quiet "${service_name}"; then
        return 0
    else
        log "ERROR: Service ${service_name} ist nicht aktiv"
        return 1
    fi
}

# Prüfe HTTP Health Endpoint
check_http_health() {
    local retries=0
    
    while [[ $retries -lt $MAX_RETRIES ]]; do
        if curl -f -s "${HEALTH_URL}" > /dev/null 2>&1; then
            log "INFO: HTTP Health Check erfolgreich"
            return 0
        else
            retries=$((retries + 1))
            log "WARN: HTTP Health Check fehlgeschlagen (Versuch ${retries}/${MAX_RETRIES})"
            
            if [[ $retries -lt $MAX_RETRIES ]]; then
                sleep $RETRY_DELAY
            fi
        fi
    done
    
    log "ERROR: HTTP Health Check nach ${MAX_RETRIES} Versuchen fehlgeschlagen"
    return 1
}

# Prüfe Log-Dateien auf Fehler
check_logs() {
    local log_file="/opt/${APP_NAME}/logs/paperless-autofields.log"
    
    if [[ -f "${log_file}" ]]; then
        # Prüfe auf kritische Fehler in den letzten 10 Minuten
        local recent_errors=$(find "${log_file}" -mmin -10 -exec grep -c "ERROR\|CRITICAL" {} \; 2>/dev/null || echo 0)
        
        if [[ $recent_errors -gt 5 ]]; then
            log "WARN: ${recent_errors} Fehler in den letzten 10 Minuten gefunden"
            return 1
        fi
    fi
    
    return 0
}

# Prüfe Speicherverbrauch
check_memory() {
    local max_memory_mb=512
    local pid=$(pgrep -f "app/autofill.py" | head -1)
    
    if [[ -n "$pid" ]]; then
        local memory_kb=$(ps -o rss= -p "$pid" 2>/dev/null || echo 0)
        local memory_mb=$((memory_kb / 1024))
        
        if [[ $memory_mb -gt $max_memory_mb ]]; then
            log "WARN: Hoher Speicherverbrauch: ${memory_mb}MB (Limit: ${max_memory_mb}MB)"
            return 1
        fi
        
        log "INFO: Speicherverbrauch: ${memory_mb}MB"
    fi
    
    return 0
}

# Starte Service neu
restart_service() {
    local service_name="$1"
    
    log "INFO: Starte Service ${service_name} neu..."
    
    if systemctl restart "${service_name}"; then
        log "INFO: Service ${service_name} erfolgreich neugestartet"
        return 0
    else
        log "ERROR: Neustart von Service ${service_name} fehlgeschlagen"
        return 1
    fi
}

# Sende Benachrichtigung (optional)
send_notification() {
    local message="$1"
    
    # Webhook URL aus Umgebungsvariable (optional)
    if [[ -n "${WEBHOOK_URL}" ]]; then
        curl -X POST -H "Content-Type: application/json" \
             -d "{\"text\":\"${APP_NAME}: ${message}\"}" \
             "${WEBHOOK_URL}" > /dev/null 2>&1
    fi
    
    # E-Mail (optional, benötigt mailutils)
    if [[ -n "${ADMIN_EMAIL}" ]] && command -v mail >/dev/null; then
        echo "${message}" | mail -s "${APP_NAME} Alert" "${ADMIN_EMAIL}"
    fi
}

# Hauptfunktion
main() {
    log "INFO: Starte Health Check..."
    
    local issues=0
    
    # Service Status prüfen
    if ! check_service "${APP_NAME}.service"; then
        restart_service "${APP_NAME}.service"
        issues=$((issues + 1))
    fi
    
    if ! check_service "${APP_NAME}-web.service"; then
        restart_service "${APP_NAME}-web.service"
        issues=$((issues + 1))
    fi
    
    # HTTP Health Check (nur wenn Services laufen)
    if [[ $issues -eq 0 ]]; then
        if ! check_http_health; then
            restart_service "${APP_NAME}-web.service"
            issues=$((issues + 1))
        fi
    fi
    
    # Log-Dateien prüfen
    if ! check_logs; then
        issues=$((issues + 1))
    fi
    
    # Speicherverbrauch prüfen
    if ! check_memory; then
        issues=$((issues + 1))
    fi
    
    # Zusammenfassung
    if [[ $issues -eq 0 ]]; then
        log "INFO: Health Check erfolgreich - Alle Services laufen normal"
    else
        local message="Health Check abgeschlossen - ${issues} Problem(e) gefunden und behoben"
        log "WARN: ${message}"
        send_notification "${message}"
    fi
}

# Script ausführen
main "$@"

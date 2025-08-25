#!/bin/bash

# Paperless AutoFields Deployment Script
# Für Ubuntu/Debian und UGREEN NAS (Linux-basiert)

set -e

# Konfiguration
APP_NAME="paperless-autofields"
APP_USER="paperless"
APP_DIR="/opt/${APP_NAME}"
VENV_DIR="${APP_DIR}/venv"
SERVICE_FILE="/etc/systemd/system/${APP_NAME}.service"
WEB_SERVICE_FILE="/etc/systemd/system/${APP_NAME}-web.service"

# Farben für Output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Logging
log_info() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

log_warn() {
    echo -e "${YELLOW}[WARN]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Prüfe Root-Rechte
check_root() {
    if [[ $EUID -ne 0 ]]; then
        log_error "Dieses Script muss als root ausgeführt werden"
        exit 1
    fi
}

# Installiere System-Dependencies
install_system_deps() {
    log_info "Installiere System-Dependencies..."
    
    apt-get update
    apt-get install -y \
        python3 \
        python3-pip \
        python3-venv \
        git \
        curl \
        systemd \
        nginx \
        supervisor
    
    log_info "System-Dependencies installiert"
}

# Erstelle Benutzer
create_user() {
    log_info "Erstelle Benutzer ${APP_USER}..."
    
    if ! id "${APP_USER}" &>/dev/null; then
        useradd -r -s /bin/bash -d "${APP_DIR}" "${APP_USER}"
        log_info "Benutzer ${APP_USER} erstellt"
    else
        log_warn "Benutzer ${APP_USER} existiert bereits"
    fi
}

# Erstelle Verzeichnisse
setup_directories() {
    log_info "Erstelle Verzeichnisse..."
    
    mkdir -p "${APP_DIR}"
    mkdir -p "${APP_DIR}/logs"
    mkdir -p "/var/log/${APP_NAME}"
    
    chown -R "${APP_USER}:${APP_USER}" "${APP_DIR}"
    chown -R "${APP_USER}:${APP_USER}" "/var/log/${APP_NAME}"
}

# Installiere Anwendung
install_app() {
    log_info "Installiere ${APP_NAME}..."
    
    # Clone Repository oder kopiere Dateien
    if [[ -n "${REPO_URL}" ]]; then
        git clone "${REPO_URL}" "${APP_DIR}/source"
        cp -r "${APP_DIR}/source/"* "${APP_DIR}/"
        rm -rf "${APP_DIR}/source"
    else
        # Wenn lokal ausgeführt, kopiere aktuelle Dateien
        cp -r ./* "${APP_DIR}/"
    fi
    
    # Python Virtual Environment erstellen
    sudo -u "${APP_USER}" python3 -m venv "${VENV_DIR}"
    sudo -u "${APP_USER}" "${VENV_DIR}/bin/pip" install --upgrade pip
    sudo -u "${APP_USER}" "${VENV_DIR}/bin/pip" install -r "${APP_DIR}/requirements.txt"
    
    # Konfigurationsdatei erstellen
    if [[ ! -f "${APP_DIR}/.env" ]]; then
        cp "${APP_DIR}/.env.example" "${APP_DIR}/.env"
        log_warn "Bitte .env-Datei in ${APP_DIR}/.env konfigurieren"
    fi
    
    chown -R "${APP_USER}:${APP_USER}" "${APP_DIR}"
    log_info "Anwendung installiert"
}

# Installiere systemd Services
install_services() {
    log_info "Installiere systemd Services..."
    
    # Hauptservice
    cp "${APP_DIR}/systemd/${APP_NAME}.service" "${SERVICE_FILE}"
    
    # Web-Service
    cp "${APP_DIR}/systemd/${APP_NAME}-web.service" "${WEB_SERVICE_FILE}"
    
    # Services aktivieren
    systemctl daemon-reload
    systemctl enable "${APP_NAME}.service"
    systemctl enable "${APP_NAME}-web.service"
    
    log_info "systemd Services installiert"
}

# Konfiguriere Nginx (optional)
setup_nginx() {
    log_info "Konfiguriere Nginx..."
    
    cat > "/etc/nginx/sites-available/${APP_NAME}" << EOF
server {
    listen 80;
    server_name ${APP_NAME}.local;
    
    location / {
        proxy_pass http://127.0.0.1:5000;
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto \$scheme;
    }
    
    location /static/ {
        alias ${APP_DIR}/app/webui/static/;
        expires 30d;
    }
}
EOF
    
    # Site aktivieren
    ln -sf "/etc/nginx/sites-available/${APP_NAME}" "/etc/nginx/sites-enabled/"
    nginx -t && systemctl reload nginx
    
    log_info "Nginx konfiguriert"
}

# Starte Services
start_services() {
    log_info "Starte Services..."
    
    systemctl start "${APP_NAME}.service"
    systemctl start "${APP_NAME}-web.service"
    
    # Status prüfen
    sleep 5
    if systemctl is-active --quiet "${APP_NAME}.service"; then
        log_info "${APP_NAME} Service gestartet"
    else
        log_error "${APP_NAME} Service konnte nicht gestartet werden"
        systemctl status "${APP_NAME}.service"
        exit 1
    fi
    
    if systemctl is-active --quiet "${APP_NAME}-web.service"; then
        log_info "${APP_NAME}-web Service gestartet"
    else
        log_error "${APP_NAME}-web Service konnte nicht gestartet werden"
        systemctl status "${APP_NAME}-web.service"
        exit 1
    fi
}

# Health Check
health_check() {
    log_info "Führe Health Check durch..."
    
    sleep 10
    
    if curl -f http://localhost:5000/health > /dev/null 2>&1; then
        log_info "Health Check erfolgreich"
    else
        log_error "Health Check fehlgeschlagen"
        exit 1
    fi
}

# Zeige Deployment-Informationen
show_info() {
    log_info "Deployment abgeschlossen!"
    echo
    echo "Services:"
    echo "  Main: systemctl status ${APP_NAME}"
    echo "  Web:  systemctl status ${APP_NAME}-web"
    echo
    echo "Logs:"
    echo "  Main: journalctl -u ${APP_NAME} -f"
    echo "  Web:  journalctl -u ${APP_NAME}-web -f"
    echo "  App:  tail -f ${APP_DIR}/logs/paperless-autofields.log"
    echo
    echo "Web Interface: http://localhost:5000"
    echo "Konfiguration: ${APP_DIR}/.env"
    echo "Patterns: ${APP_DIR}/patterns.yaml"
    echo
    echo "Nächste Schritte:"
    echo "1. Konfiguriere ${APP_DIR}/.env mit deinen Paperless-NGX Einstellungen"
    echo "2. Starte Services neu: systemctl restart ${APP_NAME} ${APP_NAME}-web"
    echo "3. Überwache Logs für Fehler"
}

# Hauptfunktion
main() {
    log_info "Starte Deployment von ${APP_NAME}..."
    
    check_root
    install_system_deps
    create_user
    setup_directories
    install_app
    install_services
    
    # Optional: Nginx Setup
    if [[ "${SETUP_NGINX:-no}" == "yes" ]]; then
        setup_nginx
    fi
    
    start_services
    health_check
    show_info
}

# Script ausführen
main "$@"

# CHANGELOG

## [1.0.0] - 2024-08-25

### Added
- Initial release of Paperless AutoFields
- Complete modular Python architecture with app/, tests/, and webui/
- Core modules implemented:
  - config.py: Environment-based configuration management
  - api.py: Paperless-NGX REST API communication
  - extractor.py: OCR/Regex field extraction logic with live reload
  - autofill.py: Main processing loop with continuous monitoring
  - webui/gui.py: Flask-based web interface for configuration and monitoring
  - cli.py: Command-line interface for manual operations

### Features
- Multi-stage Dockerfile with amd64/arm64 support for UGREEN NAS compatibility
- docker-compose.yml with complete stack setup including health checks
- YAML-based regex patterns for invoice field extraction with examples:
  - Rechnungsnummer (Invoice number)
  - Zahlungsziel (Payment due date)
  - Betrag (Amount)
  - IBAN with checksum validation
  - Kundennummer (Customer number)
  - Kassenzeichen (Reference number)
- Live pattern reload capability without container restart
- Validation system with IBAN format checking
- Automatic document type filtering
- Custom field population via Paperless-NGX API
- Structured logging with rotation and multiple levels
- Web GUI for pattern management, testing, and monitoring
- Extensible pattern system for new field types
- Skip already processed documents option
- Comprehensive test suite with pytest and fixtures
- GitHub Actions CI/CD pipeline with multi-architecture builds
- Pre-commit hooks for code quality
- Development environment with Makefile for common tasks

### Documentation
- Complete README.md with quick start guide
- API reference documentation
- Pattern configuration examples
- Docker deployment instructions
- Development setup guide

### Development Tools
- requirements.txt and requirements-dev.txt for dependencies
- Pre-commit configuration with black, flake8, isort, mypy
- Makefile for common development tasks
- Interactive setup.py script for first-time configuration
- GitHub Actions for automated testing and Docker image builds

### Configuration
- Environment-based configuration with .env support
- Configurable processing intervals
- Flexible logging options
- Web interface port and host configuration
- Pattern file live reloading
- Validation toggle options

---

## Future Releases

### [1.1.0] - Planned Features
- Enhanced web UI with real-time updates
- Pattern import/export functionality
- Batch document processing API
- Advanced validation rules
- Email notifications for processing results
- Performance metrics and analytics
- Multi-language pattern support

### [1.2.0] - Advanced Features
- Machine learning-based field detection
- OCR quality assessment
- Document classification
- Workflow automation
- Integration with external systems
- Advanced reporting dashboard

### [2.0.0] - Major Enhancements
- Plugin system for custom extractors
- REST API for third-party integrations
- User management and authentication
- Multi-tenant support
- Advanced pattern templates
- Cloud deployment options

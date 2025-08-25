.PHONY: help install install-dev test test-cov lint format clean docker-build docker-run

# Default target
help:
	@echo "Verfügbare Kommandos:"
	@echo "  install     - Installiert Production Dependencies"
	@echo "  install-dev - Installiert Development Dependencies"
	@echo "  test        - Führt Tests aus"
	@echo "  test-cov    - Führt Tests mit Coverage aus"
	@echo "  lint        - Code-Linting mit flake8"
	@echo "  format      - Code-Formatierung mit black und isort"
	@echo "  clean       - Löscht temporäre Dateien"
	@echo "  docker-build - Baut Docker Image"
	@echo "  docker-run  - Startet Docker Container"

# Dependencies
install:
	pip install -r requirements.txt

install-dev:
	pip install -r requirements.txt -r requirements-dev.txt
	pre-commit install

# Testing
test:
	pytest tests/ -v

test-cov:
	pytest tests/ --cov=app --cov-report=html --cov-report=term-missing

test-watch:
	pytest-watch tests/ app/

# Code Quality
lint:
	flake8 app/ tests/
	mypy app/

format:
	black app/ tests/
	isort app/ tests/

format-check:
	black --check app/ tests/
	isort --check-only app/ tests/

# Cleanup
clean:
	find . -type f -name "*.pyc" -delete
	find . -type d -name "__pycache__" -delete
	find . -type d -name "*.egg-info" -exec rm -rf {} +
	rm -rf .coverage htmlcov/ .pytest_cache/ .mypy_cache/

# Docker
docker-build:
	docker build -t paperless-autofields:latest .

docker-build-multi:
	docker buildx build --platform linux/amd64,linux/arm64 -t paperless-autofields:latest .

docker-run:
	docker run --rm -it -p 5000:5000 --env-file .env paperless-autofields:latest

docker-run-web:
	docker run --rm -it -p 5000:5000 --env-file .env paperless-autofields:latest python app/webui/gui.py

# Docker Compose
compose-up:
	docker-compose up -d

compose-down:
	docker-compose down

compose-logs:
	docker-compose logs -f

# Development
dev-run:
	python app/autofill.py --once

dev-web:
	python app/webui/gui.py

dev-setup: install-dev
	cp .env.example .env
	mkdir -p logs

# Git hooks
pre-commit:
	pre-commit run --all-files

# Documentation (optional)
docs:
	sphinx-build -b html docs/ docs/_build/

# Version bump (requires bump2version)
bump-patch:
	bump2version patch

bump-minor:
	bump2version minor

bump-major:
	bump2version major

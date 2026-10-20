# UtsavAI – Makefile
# Usage: make <target>

.PHONY: install run test test-cov lint format clean help

PYTHON := python
PIP := pip
UVICORN := uvicorn

help:  ## Show this help message
	@echo "UtsavAI – Smart Celebration & Event Planner"
	@echo ""
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | awk 'BEGIN {FS = ":.*?## "}; {printf "  \033[36m%-15s\033[0m %s\n", $$1, $$2}'

install:  ## Install production dependencies
	$(PIP) install -r requirements.txt

install-dev:  ## Install development and test dependencies
	$(PIP) install -r requirements-dev.txt

run:  ## Run the development server (no reload)
	$(UVICORN) backend.main:app --host 127.0.0.1 --port 8000

dev:  ## Run with auto-reload (development)
	$(UVICORN) backend.main:app --host 127.0.0.1 --port 8000 --reload

test:  ## Run all tests
	$(PYTHON) -m pytest tests/ -v --tb=short -p no:warnings

test-cov:  ## Run tests with coverage report
	$(PYTHON) -m pytest tests/ -v --cov=backend --cov-report=term-missing --cov-report=html

test-fast:  ## Run tests without coverage (faster)
	$(PYTHON) -m pytest tests/ -v --tb=short -p no:warnings --no-cov

lint:  ## Run ruff linter
	$(PYTHON) -m ruff check backend/ tests/

format:  ## Auto-format with ruff
	$(PYTHON) -m ruff format backend/ tests/
	$(PYTHON) -m ruff check --fix backend/ tests/

clean:  ## Remove cache files and build artifacts
	find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true
	find . -type f -name "*.pyc" -delete 2>/dev/null || true
	find . -type d -name .pytest_cache -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name htmlcov -exec rm -rf {} + 2>/dev/null || true
	find . -type f -name .coverage -delete 2>/dev/null || true

setup:  ## Full setup: install dev dependencies + copy .env.example
	$(PIP) install -r requirements-dev.txt
	@if not exist .env (copy .env.example .env & echo Created .env from .env.example) else (echo .env already exists)

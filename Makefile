.PHONY: setup lint type unit build

# Prefer local virtualenv Python if present (Windows/Linux)
PYTHON ?= python
ifeq (,$(wildcard .venv))
# no venv dir, keep default
else
  ifneq (,$(wildcard .venv/Scripts/python.exe))
    PYTHON := .venv/Scripts/python.exe
  else ifneq (,$(wildcard .venv/bin/python))
    PYTHON := .venv/bin/python
  endif
endif

setup:  ## install deps
	python -m pip install -U pip
	pip install -r requirements.txt
	pre-commit install

lint:   ## ruff + black --check
	ruff check .
	black --check .

type:   ## mypy for backend
	mypy apps/backend

unit:   ## fast tests only (DDD)
	pytest -q -m "not slow" tests/ddd --maxfail=1 || true

run-backend: ## run backend API locally
ifeq ($(OS),Windows_NT)
	cmd /C "set PYTHONPATH=apps/backend && $(PYTHON) -m uvicorn apps.backend.app.api_gateway.main:app --host 0.0.0.0 --port 8000 --reload"
else
	PYTHONPATH=apps/backend $(PYTHON) -m uvicorn apps.backend.app.api_gateway.main:app --host 0.0.0.0 --port 8000 --reload
endif

openapi-export: ## export FastAPI OpenAPI to apps/backend/var/openapi.json
	python apps/backend/infra/ci/export_openapi.py --out apps/backend/var/openapi.json

run-events: ## run events relay worker
ifeq ($(OS),Windows_NT)
	cmd /C "set PYTHONPATH=apps/backend && $(PYTHON) -m apps.backend.infra.events_worker"
else
	PYTHONPATH=apps/backend $(PYTHON) -m apps.backend.infra.events_worker
endif

build:  ## optional package/build
	python -m build

.PHONY: db-revision db-upgrade db-downgrade migrate

db-revision:  ## create new alembic revision (use: make db-revision m="message")
	@if [ -z "$(m)" ]; then echo "Usage: make db-revision m=\"message\""; exit 1; fi; \
	$(PYTHON) -m alembic -c alembic.ini revision -m "$(m)"

db-upgrade:   ## upgrade DB to head
	$(PYTHON) -m alembic -c alembic.ini upgrade head

migrate: ## alias for db-upgrade
	$(PYTHON) -m alembic -c alembic.ini upgrade head

db-downgrade: ## downgrade DB one revision
	$(PYTHON) -m alembic -c alembic.ini downgrade -1

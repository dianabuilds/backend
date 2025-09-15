.PHONY: setup lint type unit build

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
	uvicorn apps.backend.app.api_gateway.main:app --host 0.0.0.0 --port 8000 --reload

openapi-export: ## export FastAPI OpenAPI to apps/backend/var/openapi.json
	python apps/backend/infra/ci/export_openapi.py --out apps/backend/var/openapi.json

run-events: ## run events relay worker
	python -m apps.backend.infra.events_worker

build:  ## optional package/build
	python -m build

.PHONY: db-revision db-upgrade db-downgrade migrate

db-revision:  ## create new alembic revision (use: make db-revision m="message")
	@if [ -z "$(m)" ]; then echo "Usage: make db-revision m=\"message\""; exit 1; fi; \
	alembic -c alembic.ini revision -m "$(m)"

db-upgrade:   ## upgrade DB to head
	alembic -c alembic.ini upgrade head

migrate: ## alias for db-upgrade
	alembic -c alembic.ini upgrade head

db-downgrade: ## downgrade DB one revision
	alembic -c alembic.ini downgrade -1

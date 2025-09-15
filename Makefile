.PHONY: setup lint type unit build

setup:  ## install deps
	python -m pip install -U pip
	pip install -r requirements.txt
	pre-commit install

lint:   ## ruff + black --check
	ruff check .
	black --check .

type:   ## mypy for DDD
	mypy apps/backendDDD

unit:   ## fast tests only (DDD)
	pytest -q -m "not slow" tests/ddd --maxfail=1 || true

run-ddd: ## run DDD API locally
	uvicorn apps.backendDDD.app.api_gateway.main:app --host 0.0.0.0 --port 8000 --reload

openapi-export: ## export FastAPI OpenAPI to apps/backendDDD/var/openapi.json
	python apps/backendDDD/infra/ci/export_openapi.py --out apps/backendDDD/var/openapi.json

run-events: ## run events relay worker
	python -m apps.backendDDD.infra.events_worker

build:  ## optional package/build
	python -m build

.PHONY: db-ddd-revision db-ddd-upgrade db-ddd-downgrade

db-ddd-revision:  ## create new DDD alembic revision (use: make db-ddd-revision m="message")
	@if [ -z "$(m)" ]; then echo "Usage: make db-ddd-revision m=\"message\""; exit 1; fi; \
	alembic -c apps/backendDDD/alembic.ini revision -m "$(m)"

db-ddd-upgrade:   ## upgrade DDD DB to head
	alembic -c apps/backendDDD/alembic.ini upgrade head

db-ddd-downgrade: ## downgrade DDD DB one revision
	alembic -c apps/backendDDD/alembic.ini downgrade -1

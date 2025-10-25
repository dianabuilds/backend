.PHONY: dev-up seed test schemas-validate clients-gen schemas-compat migrate-all eval imports-check imports-lint lint lint-fix typecheck run run-public run-admin run-ops run-relay run-events run-scheduler

# Shared API contour defaults
PYTHON ?= python
APP_API_CONTOUR ?= all
APP_PORT ?= 8000
UVICORN_HOST ?= 0.0.0.0
UVICORN_PORT ?= $(APP_PORT)
UVICORN_APP ?= apps.backend.app.api_gateway.main:app
UVICORN_RELOAD_FLAGS ?= --reload
# Default ports per contour to keep local runs in sync with docker compose
APP_PORT_PUBLIC ?= 8010
APP_PORT_ADMIN ?= 8011
APP_PORT_OPS ?= 8012

ifeq ($(OS),Windows_NT)
UVICORN_CMD = $(PYTHON) -m uvicorn $(UVICORN_APP) $(UVICORN_RELOAD_FLAGS) --host !UVICORN_HOST! --port !UVICORN_PORT!
define run_contour
	@echo "Starting API contour '$(1)' on http://$(UVICORN_HOST):$(2)"
	cmd /V:ON /C "set APP_API_CONTOUR=$(1) && set APP_PORT=$(2) && set UVICORN_HOST=$(UVICORN_HOST) && set UVICORN_PORT=$(2) && $(UVICORN_CMD)"
endef
else
UVICORN_CMD = $(PYTHON) -m uvicorn $(UVICORN_APP) $(UVICORN_RELOAD_FLAGS) --host $$UVICORN_HOST --port $$UVICORN_PORT
define run_contour
	@echo "Starting API contour '$(1)' on http://$(UVICORN_HOST):$(2)"
	APP_API_CONTOUR=$(1) APP_PORT=$(2) UVICORN_HOST=$(UVICORN_HOST) UVICORN_PORT=$(2) $(UVICORN_CMD)
endef
endif

dev-up:
	docker compose -f infra/docker-compose.yml up -d

schemas-validate:
	bash infra/ci/schemas-validate.sh

schemas-compat:
	bash infra/ci/schemas-compat.sh

clients-gen:
	bash infra/ci/clients-gen.sh

migrate-all:
	bash infra/ci/migrate_all.sh

# Apply all raw SQL DDL files in domains/*/schema/sql in lexicographic order.
migrate-ddl:
	bash infra/ci/migrate_all.sh

# Generate a domain from template: make gen-domain KIND=product NAME=demo
gen-domain:
	KIND=$${KIND:-product}; NAME=$${NAME:?set NAME}; bash infra/ci/gen_domain.sh $$KIND $$NAME

test:
	pytest -q

eval:
	echo "Run evals (placeholder)"

imports-check:
	python infra/ci/gen_import_rules.py > /tmp/import-linter.ini || true
	echo "Generated import-linter rules to /tmp/import-linter.ini"

imports-lint:
	python -m importlinter.cli lint --config importlinter.ini

lint:
	ruff check . --config pyproject.toml

lint-fix:
	ruff check . --config pyproject.toml --fix
	black .

typecheck:
	mypy . --config-file pyproject.toml

run: ## Legacy alias; prefer run-public/run-admin/run-ops
	@echo "make run is a legacy alias; prefer run-public/run-admin/run-ops"
	$(call run_contour,$(APP_API_CONTOUR),$(APP_PORT))

run-public: ## Local public contour (port $(APP_PORT_PUBLIC))
	$(call run_contour,public,$(APP_PORT_PUBLIC))

run-admin: ## Local admin contour (port $(APP_PORT_ADMIN))
	$(call run_contour,admin,$(APP_PORT_ADMIN))

run-ops: ## Local ops contour (port $(APP_PORT_OPS))
	$(call run_contour,ops,$(APP_PORT_OPS))

run-relay:
	python -c "from apps.backend.domains.platform.events.logic.relay import RedisRelay; import os; topics=os.getenv('EVENT_TOPICS','profile.updated.v1').split(','); from apps.backend.packages.core.config import load_settings; s=load_settings(); RedisRelay(s.redis_url, topics).loop(routes={t: (lambda t,p: print('event',t,p)) for t in topics})"

run-events:
	python -m apps.backend.workers events

run-scheduler:
	python -m apps.backend.workers scheduler

run-notifications:
	python -m apps.backend.workers notifications



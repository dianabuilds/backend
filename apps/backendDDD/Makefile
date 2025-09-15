.PHONY: dev-up seed test schemas-validate clients-gen schemas-compat migrate-all eval imports-check imports-lint lint typecheck run run-relay run-events

dev-up:
	docker compose -f apps/backendDDD/infra/docker-compose.yml up -d

schemas-validate:
	bash apps/backendDDD/infra/ci/schemas-validate.sh

schemas-compat:
	bash apps/backendDDD/infra/ci/schemas-compat.sh

clients-gen:
	bash apps/backendDDD/infra/ci/clients-gen.sh

migrate-all:
	bash apps/backendDDD/infra/ci/migrate_all.sh

# Apply all raw SQL DDL files in domains/*/schema/sql in lexicographic order.
migrate-ddl:
	APP_DATABASE_URL=$${APP_DATABASE_URL:-postgresql://app:app@localhost:5432/app} bash apps/backendDDD/infra/ci/migrate_all.sh

# Generate a domain from template: make gen-domain KIND=product NAME=demo
gen-domain:
	KIND=$${KIND:-product}; NAME=$${NAME:?set NAME}; bash apps/backendDDD/infra/ci/gen_domain.sh $$KIND $$NAME

test:
	pytest -q

eval:
	echo "Run evals (placeholder)"

imports-check:
	python apps/backendDDD/infra/ci/gen_import_rules.py > /tmp/import-linter.ini || true
	echo "Generated import-linter rules to /tmp/import-linter.ini"

imports-lint:
	python apps/backendDDD/infra/ci/gen_import_rules.py > /tmp/import-linter.ini
	lint-imports -c /tmp/import-linter.ini

lint:
	ruff check apps/backendDDD --config apps/backendDDD/pyproject.toml

typecheck:
	mypy apps/backendDDD --config-file apps/backendDDD/pyproject.toml

run:
	uvicorn apps.backendDDD.app.api_gateway.main:app --reload

run-relay:
	python -c "from apps.backendDDD.domains.platform.events.logic.relay import RedisRelay; import os; topics=os.getenv('EVENT_TOPICS','profile.updated.v1').split(','); from apps.backendDDD.packages.core.config import load_settings; s=load_settings(); RedisRelay(s.redis_url, topics).loop(routes={t: (lambda t,p: print('event',t,p)) for t in topics})"

run-events:
	python -m apps.backendDDD.infra.events_worker

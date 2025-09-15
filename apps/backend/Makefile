.PHONY: dev-up seed test schemas-validate clients-gen schemas-compat migrate-all eval imports-check imports-lint lint typecheck run run-relay run-events

dev-up:
	docker compose -f apps/backend/infra/docker-compose.yml up -d

schemas-validate:
	bash apps/backend/infra/ci/schemas-validate.sh

schemas-compat:
	bash apps/backend/infra/ci/schemas-compat.sh

clients-gen:
	bash apps/backend/infra/ci/clients-gen.sh

migrate-all:
	bash apps/backend/infra/ci/migrate_all.sh

# Apply all raw SQL DDL files in domains/*/schema/sql in lexicographic order.
migrate-ddl:
	APP_DATABASE_URL=$${APP_DATABASE_URL:-postgresql://app:app@localhost:5432/app} bash apps/backend/infra/ci/migrate_all.sh

# Generate a domain from template: make gen-domain KIND=product NAME=demo
gen-domain:
	KIND=$${KIND:-product}; NAME=$${NAME:?set NAME}; bash apps/backend/infra/ci/gen_domain.sh $$KIND $$NAME

test:
	pytest -q

eval:
	echo "Run evals (placeholder)"

imports-check:
	python apps/backend/infra/ci/gen_import_rules.py > /tmp/import-linter.ini || true
	echo "Generated import-linter rules to /tmp/import-linter.ini"

imports-lint:
	python apps/backend/infra/ci/gen_import_rules.py > /tmp/import-linter.ini
	lint-imports -c /tmp/import-linter.ini

lint:
	ruff check apps/backend --config apps/backend/pyproject.toml

typecheck:
	mypy apps/backend --config-file apps/backend/pyproject.toml

run:
	uvicorn apps.backend.app.api_gateway.main:app --reload

run-relay:
	python -c "from apps.backend.domains.platform.events.logic.relay import RedisRelay; import os; topics=os.getenv('EVENT_TOPICS','profile.updated.v1').split(','); from apps.backend.packages.core.config import load_settings; s=load_settings(); RedisRelay(s.redis_url, topics).loop(routes={t: (lambda t,p: print('event',t,p)) for t in topics})"

run-events:
	python -m apps.backend.infra.events_worker

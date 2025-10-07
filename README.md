# Caves Monorepo

This repository hosts two major applications:

- `apps/backend`  FastAPI service with domain-driven modules, Alembic migrations, tasks, and tooling.
- `apps/web`  React frontend (Vite) that consumes the backend APIs.

## Backend

All backend sources and configuration live under `apps/backend`:

```
### Domain layout

Bounded contexts under `apps/backend/domains/` share a layered layout so use-cases stay infrastructure-agnostic:

- `api/` contains transport adapters (FastAPI routers, task handlers, CLI).
- `application/` hosts the use-case layer (commands, queries, services, DTOs).
- `adapters/sql/` and `adapters/memory/` provide infrastructure for Postgres and deterministic fallbacks respectively; other adapter families (Redis, files) live alongside.
- `domain/` keeps entities, value objects, and policies.

Use-cases talk only to ports defined in `application` / `domain`, which keeps swapping adapters a configuration detail.


### Billing domain snapshot

- `domains/platform/billing/application/use_cases`   `BillingUseCases`   `public`, `admin`,     `settings.BillingSettingsUseCase`,   `apps/backend/app/api_gateway/settings/billing.py`  payload     .
-    `domains/platform/billing/infrastructure/sql`:    summary/history  ;      `BillingSummaryRepo`/`BillingHistoryRepo`.
-  unit-   `tests/unit/billing`, smoke-  `tests/smoke/test_api_billing.py`.

apps/backend/
  +-- app/                # FastAPI entrypoints and wiring
  +-- domains/            # DDD modules (platform, product, ...)
  +-- packages/           # Shared libraries (config, db, schemas)
  +-- migrations/         # Alembic scripts (0100_squashed_base + legacy/)
  +-- infra/              # Dev/CI tooling and scripts
  +-- requirements.txt    # Runtime + dev dependencies
  L-- pyproject.toml      # Tooling configuration (ruff, black, mypy, pytest)
```

### Quick start

```bash
cd apps/backend
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate
pip install -r requirements.txt
# optional: pip install -e .

# Run migrations against a dev database
echo APP_DATABASE_URL=... >> .env
python -m alembic -c alembic.ini upgrade head

# Launch the API
uvicorn apps.backend.app.api_gateway.main:app --reload
```
Backend можно открывать в IDE прямо из каталога apps/backend: shim apps.backend (см. apps/backend/apps/backend/__init__.py) держит импорты apps.backend.* без необходимости добавлять родительскую директорию в PYTHONPATH.

Hooks and linters:

```bash
# one-off
pre-commit install --config apps/backend/.pre-commit-config.yaml
# manual run
pre-commit run --all-files --config apps/backend/.pre-commit-config.yaml

make -C apps/backend lint
make -C apps/backend type
```

Alembic now uses the squashed baseline `0100_squashed_base`. Legacy migrations are archived under `apps/backend/migrations/legacy/` and are invoked automatically by the squashed script when applying to a clean database.

## Frontend

The React app is under `apps/web` (see `apps/web/README.md`). Typical workflow:

```bash
cd apps/web
npm install
npm run dev
```

## Tests

Backend tests live in the repository root under `tests/`. Use the backend pytest config:

```bash
pytest -c apps/backend/pytest.ini
```

---

If you need to add repository-level tooling, prefer wiring it through the respective `apps/<module>` directory to avoid duplicating configuration in the repo root.

## Documentation

Backend docs live in `apps/backend/docs/` (ADR, knowledge base, etc.).
### Test mode

The backend exposes a unified test mode switch via `packages.core.testing.is_test_mode()`. When the mode is active (for example `APP_ENV=test` or whenever pytest bootstraps), all domain containers fall back to in-memory adapters for Postgres, Redis, audit logging, notifications, and events. External services are never touched during startup or tests.

In test mode the following fallbacks are enabled:

- Platform events use the in-process `InMemoryOutbox`/`InMemoryEventBus`, so events are synchronous and not durable.
- Platform notifications store templates, preferences, and inbox messages in-memory; email/webhook channels log only.
- Platform audit writes to `InMemoryAuditRepo`, meaning admin activity is not persisted.
- Platform moderation skips the Postgres snapshot; state changes live only for the process lifetime.
- Product repos (nodes, profile, achievements, quests, referrals, tags, worlds) fall back to seeded memory adapters with no cross-test persistence.
- Search uses the in-memory index and cache, ignoring Redis and `search_persist_path`.

To run the full backend test suite locally use the PowerShell helper, which configures the environment automatically:

```
./scripts/run-tests.ps1
```

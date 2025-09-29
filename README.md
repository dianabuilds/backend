# Caves Monorepo

This repository hosts two major applications:

- `apps/backend` – FastAPI service with domain-driven modules, Alembic migrations, tasks, and tooling.
- `apps/web` – React frontend (Vite) that consumes the backend APIs.

## Backend

All backend sources and configuration live under `apps/backend`:

```
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
uvicorn app.api_gateway.main:app --reload
```

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

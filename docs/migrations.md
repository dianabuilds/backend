# Database Migrations

This project uses Alembic for schema migrations.

## Squashed Baseline (2025‑09‑13)

All previous revisions were squashed into a single baseline
`20250913_squashed_initial`. This file creates the current schema directly
from SQLAlchemy models.

- Existing databases already on the old head:
  - Stamp the new baseline without running historical migrations:
    ```bash
    alembic stamp 20250913_squashed_initial
    ```
- New databases / fresh environments:
  - Create schema from scratch:
    ```bash
    alembic upgrade head
    ```

## Creating a new migration

1. Ensure the DB is at head: `alembic upgrade head`.
2. Make your model changes.
3. Generate: `alembic revision --autogenerate -m "<summary>"`.
4. Review and apply: `alembic upgrade head`.

## CI checks

We recommend adding workflow steps to verify migrations:
- `alembic upgrade head` against a disposable database
- `alembic downgrade -1` and back to `head`
- Ensure a single head: `alembic heads` → 1 result

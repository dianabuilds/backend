# Database Migrations

This project uses [Alembic](https://alembic.sqlalchemy.org/) for schema migrations.

## Creating a Migration

1. Make sure the database schema is up to date:
   ```bash
   alembic upgrade head
   ```
2. Generate a new migration based on model changes:
   ```bash
   alembic revision --autogenerate -m "describe change"
   ```
3. Review the generated script under `apps/backend/alembic/versions/` and adjust if needed.
4. Apply the migration:
   ```bash
   alembic upgrade head
   ```

## Verifying Migrations

To ensure models match the database, run:
```bash
pytest tests/unit/test_migrations.py
```
Set `RUN_DB_TESTS=1` to execute migration checks against a real database.

## Backfilling Missing Content Items

To create `content_items` for legacy `nodes` that lack them, run the latest
migration:

```bash
alembic upgrade head
```

This scans the `nodes` table and inserts a corresponding `content_items` record
for each node without one.

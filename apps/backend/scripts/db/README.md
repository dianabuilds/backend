# Database Maintenance Scripts

These scripts help with aggressive cleanup and renaming in a PostgreSQL database. They are intended for development or controlled migrations with backups.

## Prerequisites

- PostgreSQL connection string in `DATABASE_URL` (or pass to `psql` directly).
- Alembic configured in this repo (migrations env at `apps/backend/migrations`).

## 1) Nuke-and-rebuild (drop all tables)

Destructive: drops all user tables in the current schema. Use only if data can be lost.

```
psql "$DATABASE_URL" -v ON_ERROR_STOP=1 -f apps/backend/scripts/db/reset_database.sql

# Optional but recommended: reset Alembic history and rebuild schema
alembic stamp base
alembic upgrade head
```

Notes:

- If you also want to drop the `alembic_version` table, uncomment the lines in the SQL.
- The script enables `pgcrypto` to allow `gen_random_uuid()` by default.

## 2) Remove the `product_` prefix from tables

This script renames `product_*` tables to the same name without prefix. If an unprefixed table already exists, the `product_*` table is dropped instead of renamed to avoid conflicts.

```
psql "$DATABASE_URL" -v ON_ERROR_STOP=1 -f apps/backend/scripts/db/rename_product_tables.sql
```

## 3) ID strategy

If switching IDs, prefer UUIDs with server defaults in Postgres:

```python
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID

id = sa.Column(
    UUID(as_uuid=True),
    primary_key=True,
    server_default=sa.text('gen_random_uuid()')  # requires pgcrypto
)
```

Alembic snippet to ensure the extension exists in an upgrade:

```python
from alembic import op
op.execute("CREATE EXTENSION IF NOT EXISTS pgcrypto")
```

If you want time-ordered UUIDs (UUIDv7), we can add a custom function/extension, but plain UUIDv4 via `gen_random_uuid()` is widely supported and simple.

## 4) Suggested workflow for a clean v2 schema

1. Backup the current DB.
2. Run the reset script (or just the `product_` rename if that’s the only change).
3. `alembic stamp base` to drop existing revision history from the DB.
4. Implement a new baseline migration that creates only the tables you need with final names.
5. `alembic upgrade head` to build the clean schema.

For production, we should convert the reset logic into a proper, reversible migration plan with clear cutover steps and maintenance window.


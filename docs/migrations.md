# Database Migrations

This project uses [Alembic](https://alembic.sqlalchemy.org/) for schema migrations.

## Squashed Base Revision

As of 2025-09-05, all previous migrations were squashed into a new base revision `0001_base`.
Upgrade existing databases to this revision before applying future migrations.

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

## Bigint IDs

The migration in `content_items_bigint_migration.md` converts `content_items`
and `node_patches` identifiers to bigint sequences. Refer to that document for
upgrade and rollback instructions.

## Moderation Tables

Migration `20260120_create_moderation_tables` adds the core moderation schema:

- `moderation_cases` — tracked cases, indexed by `status`, `assignee_id`, `created_at`.
- `moderation_labels` — reusable labels for categorising cases.
- `case_labels` — association table between cases and labels.
- `case_notes` — freeform notes linked to a case.
- `case_attachments` — file references attached to a case.
- `case_events` — history of case events and status changes.

Apply with:

```bash
alembic upgrade head
```

## Remove Obsolete Moderation Flag

Migration `20260122_remove_moderation_flag` removes the deprecated
`moderation.enabled` feature flag record from the database:

```bash
alembic upgrade head
```

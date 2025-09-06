# Account Migration

## Changelog
- Replaced workspace terminology with account in documentation.
- Dropped foreign keys and indexes on `workspace_id`.

## Developer Notes
1. Update integrations to send `account_id` instead of `workspace_id`.
2. Replace HTTP header `X-BlockSketch-Workspace-Id` with `X-BlockSketch-Account-Id`.
3. Apply the Alembic migration: `alembic upgrade head`.

## Operator Notes
1. Run the migration and verify it completes: `alembic upgrade head`.
2. Check that no residual indexes or foreign keys on `workspace_id` remain.
3. Restart API and worker processes to pick up the new schema.

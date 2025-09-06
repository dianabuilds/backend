# Account Migration

## Changelog
- Unified account terminology across documentation.
- Dropped legacy foreign keys and indexes tied to previous tenant IDs.

## Developer Notes
1. Update integrations to send `account_id` in the `X-BlockSketch-Account-Id` header.
2. Apply the Alembic migration: `alembic upgrade head`.

## Operator Notes
1. Run the migration and verify it completes: `alembic upgrade head`.
2. Ensure no residual indexes or foreign keys from the deprecated model remain.
3. Restart API and worker processes to pick up the new schema.

# Remove legacy spaces

## Changelog
- Dropped `space_id` columns and removed `spaces` and `space_members` tables.
- Added `account_id` columns and indexes to transition data to the account-based schema.

## Developer Notes
1. Apply Alembic migration `20250201_remove_spaces`: `alembic upgrade head`.
2. Update any remaining integrations to use `account_id` only.

## Operator Notes
1. Run the migration and confirm that `spaces` tables are absent.
2. Restart API and worker services after deployment.

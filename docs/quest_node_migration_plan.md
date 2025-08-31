# Quest ↔ Node Migration Plan

This runbook describes how to deploy the new quest/node models and admin screens
without disrupting existing functionality. It also covers the cleanup of legacy
structures and provides a rollback strategy.

## 1. Deploy new models and migrations

1. Generate and apply migrations that add the new quest/node models:
   ```bash
   alembic upgrade head
   ```
2. Deploy the application code containing the new models **alongside** the old
   implementation. Do not remove legacy code paths yet.
3. Gate the new admin screens behind a feature flag (e.g. `NEW_ADMIN_UI`) and
   enable the flag only for a limited group of test users.
4. Monitor logs and metrics for any errors.

## 2. Disable legacy quest↔node integration

1. After the new screens and models are verified, switch the feature flag to
   disable the legacy quest↔node integration.
2. Remove configuration or background jobs that reference the old
   integration.
3. Create a new migration to drop obsolete columns and tables. Apply it only
   after data has been migrated and validated:
   ```bash
   alembic revision -m "drop legacy quest-node tables"
   alembic upgrade head
   ```

## 3. Backups and rollback

1. **Before** running destructive migrations, create a database backup:
   ```bash
   pg_dump $DATABASE_URL > backup.sql
   ```
2. To rollback, restore the backup and downgrade migrations to the previous
   revision:
   ```bash
   psql $DATABASE_URL < backup.sql
   alembic downgrade <previous_revision>
   ```
3. Redeploy the prior application version and re-enable the legacy
   integration if necessary.

Document the outcome of each step and keep backups until the new
implementation has been verified in production.

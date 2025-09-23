-- WARNING: This script is destructive. It drops all user tables in the
-- current schema. Use only on dev/staging or when you have backups.
--
-- Usage (PostgreSQL):
--   psql "$DATABASE_URL" -v ON_ERROR_STOP=1 -f apps/backend/scripts/db/reset_database.sql
--   # Optional: reset Alembic history to base and rebuild
--   # alembic stamp base && alembic upgrade head

DO $$
DECLARE
    r record;
    cur_schema text := current_schema();
BEGIN
    -- Drop all foreign key constraints first (safest when not using CASCADE everywhere)
    FOR r IN (
        SELECT conrelid::regclass AS table_name, conname
        FROM pg_constraint
        WHERE contype = 'f' AND connamespace = current_schema()::regnamespace
    ) LOOP
        EXECUTE format('ALTER TABLE %s DROP CONSTRAINT IF EXISTS %I', r.table_name, r.conname);
    END LOOP;

    -- Drop all tables in current schema, excluding Alembic version table for easier stamping
    FOR r IN (
        SELECT tablename
        FROM pg_tables
        WHERE schemaname = cur_schema
          AND tablename <> 'alembic_version'
    ) LOOP
        EXECUTE format('DROP TABLE IF EXISTS %I.%I CASCADE', cur_schema, r.tablename);
        RAISE NOTICE 'Dropped table %.%', cur_schema, r.tablename;
    END LOOP;

    -- Optionally drop the Alembic version table as well; comment out if you prefer to keep it
    -- EXECUTE format('DROP TABLE IF EXISTS %I.%I', cur_schema, 'alembic_version');
    -- RAISE NOTICE 'Dropped table %.%', cur_schema, 'alembic_version';
END $$;

-- Optional: keep useful extensions ready
CREATE EXTENSION IF NOT EXISTS pgcrypto; -- for gen_random_uuid()


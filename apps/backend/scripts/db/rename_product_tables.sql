-- Rename or drop tables that start with the prefix "".
-- If an unprefixed name already exists, the prefixed table is dropped.
-- Otherwise, it is renamed to the unprefixed name.
--
-- Usage (PostgreSQL):
--   psql "$DATABASE_URL" -v ON_ERROR_STOP=1 -f apps/backend/scripts/db/rename_tables.sql

DO $$
DECLARE
    r record;
    target text;
    schema_name text := current_schema();
BEGIN
    FOR r IN (
        SELECT table_name
        FROM information_schema.tables
        WHERE table_schema = schema_name
          AND table_type = 'BASE TABLE'
          AND table_name LIKE 'product\_%'
        ORDER BY table_name
    ) LOOP
        target := substring(r.table_name from 9);  -- remove leading ''

        IF to_regclass(format('%I.%I', schema_name, target)) IS NULL THEN
            EXECUTE format('ALTER TABLE %I.%I RENAME TO %I', schema_name, r.table_name, target);
            RAISE NOTICE 'Renamed table %.% -> %', schema_name, r.table_name, target;
        ELSE
            EXECUTE format('DROP TABLE IF EXISTS %I.%I CASCADE', schema_name, r.table_name);
            RAISE NOTICE 'Dropped product table %.% because % already exists', schema_name, r.table_name, target;
        END IF;
    END LOOP;
END $$;


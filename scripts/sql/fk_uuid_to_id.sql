-- Procedure to backfill FK id columns based on matching UUID columns.
-- Usage example:
--   CALL backfill_fk_id('node_notification_settings', 'id', 'node_alt_id', 'node_id', 1000);

CREATE OR REPLACE PROCEDURE backfill_fk_id(
    p_table text,
    p_pk_col text,
    p_uuid_col text,
    p_id_col text,
    p_batch_size integer DEFAULT 1000
)
LANGUAGE plpgsql
AS $$
DECLARE
    v_rows integer;
    v_sql text;
BEGIN
    LOOP
        v_sql := format(
            'WITH batch AS (
                 SELECT %2$I, %3$I FROM %1$I
                 WHERE %4$I IS NULL
                 LIMIT %5$s
             )
             UPDATE %1$I t
             SET %4$I = n.id
             FROM nodes n
             WHERE t.%2$I IN (SELECT %2$I FROM batch)
               AND n.alt_id = t.%3$I',
            p_table, p_pk_col, p_uuid_col, p_id_col, p_batch_size
        );
        EXECUTE v_sql;
        GET DIAGNOSTICS v_rows = ROW_COUNT;
        EXIT WHEN v_rows = 0;
        COMMIT;
    END LOOP;
END;
$$;

-- Generic trigger function that fills *_id columns from *_uuid on insert or update.
CREATE OR REPLACE FUNCTION fill_fk_id_from_uuid()
RETURNS trigger
LANGUAGE plpgsql
AS $$
DECLARE
    v_uuid uuid;
    v_id bigint;
BEGIN
    v_uuid := (to_jsonb(NEW)->>TG_ARGV[1])::uuid;
    IF v_uuid IS NULL THEN
        RETURN NEW;
    END IF;

    SELECT id INTO v_id FROM nodes WHERE alt_id = v_uuid;
    IF v_id IS NULL THEN
        RETURN NEW;
    END IF;

    NEW := jsonb_populate_record(NEW, jsonb_build_object(TG_ARGV[0], v_id));
    RETURN NEW;
END;
$$;

-- Generic trigger function that blocks writes to deprecated UUID columns.
CREATE OR REPLACE FUNCTION prevent_uuid_write()
RETURNS trigger
LANGUAGE plpgsql
AS $$
BEGIN
    IF TG_OP = 'INSERT' AND (to_jsonb(NEW)->>TG_ARGV[0]) IS NOT NULL THEN
        RAISE EXCEPTION '% column is deprecated, use %', TG_ARGV[0], TG_ARGV[1];
    END IF;

    IF TG_OP = 'UPDATE'
       AND (to_jsonb(NEW)->>TG_ARGV[0]) IS DISTINCT FROM (to_jsonb(OLD)->>TG_ARGV[0]) THEN
        RAISE EXCEPTION '% column is immutable, use %', TG_ARGV[0], TG_ARGV[1];
    END IF;

    RETURN NEW;
END;
$$;

-- Example trigger setup forbidding writes to node_alt_id in node_notification_settings
DROP TRIGGER IF EXISTS trg_node_notification_settings_fill_node_id ON node_notification_settings;
DROP TRIGGER IF EXISTS trg_node_notification_settings_block_node_alt_id ON node_notification_settings;
CREATE TRIGGER trg_node_notification_settings_block_node_alt_id
BEFORE INSERT OR UPDATE ON node_notification_settings
FOR EACH ROW EXECUTE FUNCTION prevent_uuid_write('node_alt_id', 'node_id');

"""drop workspace_id constraints"""

from __future__ import annotations

from alembic import op
import sqlalchemy as sa

revision = "20241215_drop_workspace_constraints"
down_revision = "20241210_slug_scoped_by_workspace"
branch_labels = None
depends_on = None


def upgrade() -> None:
    conn = op.get_bind()
    conn.execute(
        sa.text(
            """
            DO $$
            DECLARE
                r record;
            BEGIN
                FOR r IN
                    SELECT conrelid::regclass AS table_name, conname
                    FROM pg_constraint
                    JOIN pg_class ON conrelid = pg_class.oid
                    JOIN pg_attribute ON attrelid = conrelid AND attnum = ANY(conkey)
                    WHERE pg_attribute.attname = 'workspace_id'
                      AND contype IN ('f', 'u')
                LOOP
                    EXECUTE format('ALTER TABLE %s DROP CONSTRAINT %I', r.table_name, r.conname);
                END LOOP;
                FOR r IN
                    SELECT indexrelid::regclass AS index_name
                    FROM pg_index
                    JOIN pg_class c ON c.oid = pg_index.indrelid
                    JOIN pg_attribute a ON a.attrelid = c.oid AND a.attnum = ANY(pg_index.indkey)
                    WHERE a.attname = 'workspace_id'
                      AND NOT EXISTS (
                          SELECT 1
                          FROM pg_constraint
                          WHERE conindid = pg_index.indexrelid
                      )
                LOOP
                    EXECUTE format('DROP INDEX IF EXISTS %s', r.index_name);
                END LOOP;
            END $$;
            """
        )
    )


def downgrade() -> None:
    raise NotImplementedError("downgrade not supported")

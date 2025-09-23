"""
Add status/publish_at/unpublish_at to nodes and backfill

Revision ID: 0007
Revises: 0006
Create Date: 2025-09-19

"""

from __future__ import annotations

from alembic import op

# revision identifiers, used by Alembic.
revision = "0007"
down_revision = "0006"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Add columns if not exist
    op.execute("ALTER TABLE nodes ADD COLUMN IF NOT EXISTS status text")
    op.execute("ALTER TABLE nodes ADD COLUMN IF NOT EXISTS publish_at timestamptz NULL")
    op.execute("ALTER TABLE nodes ADD COLUMN IF NOT EXISTS unpublish_at timestamptz NULL")
    # Backfill status: published if is_public=true else draft
    op.execute(
        "UPDATE nodes SET status = CASE WHEN is_public THEN 'published' ELSE 'draft' END WHERE status IS NULL"
    )
    # Add CHECK constraint for allowed values (compat: no IF NOT EXISTS for constraints)
    op.execute(
        """
        DO $$
        BEGIN
            IF NOT EXISTS (
                SELECT 1
                FROM pg_constraint
                WHERE conname = 'nodes_status_chk'
                  AND conrelid = 'nodes'::regclass
            ) THEN
                ALTER TABLE nodes
                  ADD CONSTRAINT nodes_status_chk
                  CHECK (status IN ('draft','scheduled','published','scheduled_unpublish','archived','deleted'));
            END IF;
        END$$;
        """
    )
    # Not null
    op.execute("ALTER TABLE nodes ALTER COLUMN status SET NOT NULL")
    # Indexes for scheduling
    op.execute("CREATE INDEX IF NOT EXISTS ix_nodes_status_publish_at ON nodes(status, publish_at)")
    op.execute(
        "CREATE INDEX IF NOT EXISTS ix_nodes_status_unpublish_at ON nodes(status, unpublish_at)"
    )


def downgrade() -> None:
    op.execute("DROP INDEX IF EXISTS ix_nodes_status_publish_at")
    op.execute("DROP INDEX IF EXISTS ix_nodes_status_unpublish_at")
    op.execute("ALTER TABLE nodes DROP CONSTRAINT IF EXISTS nodes_status_chk")
    op.execute("ALTER TABLE nodes DROP COLUMN IF EXISTS publish_at")
    op.execute("ALTER TABLE nodes DROP COLUMN IF EXISTS unpublish_at")
    op.execute("ALTER TABLE nodes DROP COLUMN IF EXISTS status")

"""convert content_items.node_id to integer

Revision ID: 20251226_convert_content_items_node_id
Revises: 20251225_finalize_node_id_migration
Create Date: 2025-12-26
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = "20251226_convert_content_items_node_id"
down_revision = "20251225_finalize_node_id_migration"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute(
        "ALTER TABLE content_items "
        "DROP CONSTRAINT IF EXISTS content_items_node_id_fkey"
    )
    op.execute("DROP INDEX IF EXISTS ix_content_items_node_id")
    op.alter_column("content_items", "node_id", new_column_name="node_alt_id")
    op.add_column(
        "content_items",
        sa.Column("node_id", sa.BigInteger(), nullable=True),
    )
    op.create_index("ix_content_items_node_id", "content_items", ["node_id"])
    op.create_foreign_key(
        "content_items_node_id_fkey",
        "content_items",
        "nodes",
        ["node_id"],
        ["id"],
        ondelete="CASCADE",
    )
    op.execute(
        """
        UPDATE content_items ci
        SET node_id = n.id
        FROM nodes n
        WHERE ci.node_alt_id = n.alt_id
        """
    )
    # ``node_alt_id`` may be NULL for legacy rows where the ``node_id`` column was
    # never backfilled.  For those rows the corresponding entry in ``nodes`` can
    # still be located via ``content_items.id`` matching ``nodes.alt_id``.  This
    # secondary update links such orphaned rows to their node before applying the
    # NOT NULL constraint.
    op.execute(
        """
        UPDATE content_items ci
        SET node_id = n.id
        FROM nodes n
        WHERE ci.node_id IS NULL AND n.alt_id = ci.id
        """
    )
    op.alter_column("content_items", "node_id", nullable=False)
    op.drop_column("content_items", "node_alt_id")


def downgrade() -> None:
    op.add_column(
        "content_items",
        sa.Column("node_alt_id", postgresql.UUID(as_uuid=True), nullable=True),
    )
    op.execute(
        """
        UPDATE content_items ci
        SET node_alt_id = n.alt_id
        FROM nodes n
        WHERE ci.node_id = n.id
        """
    )
    op.alter_column("content_items", "node_alt_id", nullable=True)
    op.execute(
        "ALTER TABLE content_items "
        "DROP CONSTRAINT IF EXISTS content_items_node_id_fkey"
    )
    op.execute("DROP INDEX IF EXISTS ix_content_items_node_id")
    op.drop_column("content_items", "node_id")
    op.alter_column("content_items", "node_alt_id", new_column_name="node_id")
    op.create_index("ix_content_items_node_id", "content_items", ["node_id"])
    op.create_foreign_key(
        "content_items_node_id_fkey",
        "content_items",
        "nodes",
        ["node_id"],
        ["alt_id"],
        ondelete="CASCADE",
    )

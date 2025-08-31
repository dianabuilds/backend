"""add node_id fk to node_notification_settings

Revision ID: 20251224_add_node_id_to_node_notification_settings
Revises: 20251223_add_numeric_id_to_nodes
Create Date: 2025-12-24
"""

from alembic import op
import sqlalchemy as sa

revision = "20251224_add_node_id_to_node_notification_settings"
down_revision = "20251223_add_numeric_id_to_nodes"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.alter_column(
        "node_notification_settings",
        "node_id",
        new_column_name="node_alt_id",
    )
    op.add_column(
        "node_notification_settings",
        sa.Column("node_id", sa.BigInteger(), nullable=True),
    )
    op.create_index(
        "ix_node_notification_settings_node_id",
        "node_notification_settings",
        ["node_id"],
    )
    op.create_foreign_key(
        "node_notification_settings_node_id_fkey",
        "node_notification_settings",
        "nodes",
        ["node_id"],
        ["id"],
    )
    op.execute(
        """
        UPDATE node_notification_settings nns
        SET node_id = n.id
        FROM nodes n
        WHERE nns.node_alt_id = n.alt_id
        """
    )
    op.alter_column("node_notification_settings", "node_id", nullable=False)


def downgrade() -> None:
    op.alter_column("node_notification_settings", "node_id", nullable=True)
    op.drop_constraint(
        "node_notification_settings_node_id_fkey",
        "node_notification_settings",
        type_="foreignkey",
    )
    op.drop_index(
        "ix_node_notification_settings_node_id",
        table_name="node_notification_settings",
    )
    op.drop_column("node_notification_settings", "node_id")
    op.alter_column(
        "node_notification_settings",
        "node_alt_id",
        new_column_name="node_id",
    )

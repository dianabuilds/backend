"""switch nodes primary key to id and drop node_alt_id column"""

from alembic import op
import sqlalchemy as sa

revision = "20251225_finalize_node_id_migration"
down_revision = "20251224_add_node_id_to_node_notification_settings"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Switch primary key on nodes
    op.execute("ALTER TABLE nodes DROP CONSTRAINT nodes_pkey CASCADE")
    op.create_primary_key("nodes_pkey", "nodes", ["id"])
    op.create_unique_constraint("ux_nodes_alt_id", "nodes", ["alt_id"])

    # Remove deprecated UUID column from node_notification_settings
    op.drop_constraint(
        "node_notification_settings_node_alt_id_fkey",
        "node_notification_settings",
        type_="foreignkey",
        if_exists=True,
    )
    op.drop_column(
        "node_notification_settings",
        "node_alt_id",
        if_exists=True,
    )


def downgrade() -> None:
    # Recreate node_alt_id column
    op.add_column(
        "node_notification_settings",
        sa.Column(
            "node_alt_id", sa.dialects.postgresql.UUID(as_uuid=True), nullable=True
        ),
    )
    op.execute(
        """
        UPDATE node_notification_settings nns
        SET node_alt_id = n.alt_id
        FROM nodes n
        WHERE nns.node_id = n.id
        """
    )
    op.alter_column("node_notification_settings", "node_alt_id", nullable=False)
    op.create_foreign_key(
        "node_notification_settings_node_alt_id_fkey",
        "node_notification_settings",
        "nodes",
        ["node_alt_id"],
        ["alt_id"],
        ondelete="CASCADE",
    )

    # Restore primary key on nodes
    op.drop_constraint("ux_nodes_alt_id", "nodes", type_="unique")
    op.execute("ALTER TABLE nodes DROP CONSTRAINT nodes_pkey CASCADE")
    op.create_primary_key("nodes_pkey", "nodes", ["alt_id"])

from __future__ import annotations

from alembic import op
import sqlalchemy as sa


revision = "20260117_drop_nodes_alt_id"
down_revision = "20260116_content_items_node_idx_backfill"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.drop_constraint("ux_nodes_alt_id", "nodes", type_="unique")
    op.drop_column("nodes", "alt_id")


def downgrade() -> None:
    op.add_column(
        "nodes",
        sa.Column(
            "alt_id",
            sa.dialects.postgresql.UUID(as_uuid=True),
            nullable=True,
            server_default=sa.text("gen_random_uuid()"),
        ),
    )
    op.alter_column("nodes", "alt_id", server_default=None, nullable=False)
    op.create_unique_constraint("ux_nodes_alt_id", "nodes", ["alt_id"])

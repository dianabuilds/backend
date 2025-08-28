"""add node_id foreign key to content_items"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = "20251218_add_node_id_fk"
down_revision = "20251217_merge_heads"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "content_items",
        sa.Column("node_id", postgresql.UUID(as_uuid=True), nullable=True),
    )
    op.create_index(
        "ix_content_items_node_id",
        "content_items",
        ["node_id"],
    )
    op.create_foreign_key(
        "content_items_node_id_fkey",
        "content_items",
        "nodes",
        ["node_id"],
        ["id"],
        ondelete="CASCADE",
    )


def downgrade() -> None:
    op.drop_constraint(
        "content_items_node_id_fkey",
        "content_items",
        type_="foreignkey",
    )
    op.drop_index("ix_content_items_node_id", table_name="content_items")
    op.drop_column("content_items", "node_id")

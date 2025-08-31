"""add navigation_cache table"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = "20251216_add_navigation_cache_table"
down_revision = "20251215_merge_heads"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "navigation_cache",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("node_slug", sa.String(), nullable=False, unique=True),
        sa.Column(
            "navigation", postgresql.JSONB(astext_type=sa.Text()), nullable=False
        ),
        sa.Column("compass", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column("echo", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column(
            "generated_at", sa.DateTime(), nullable=False, server_default=sa.func.now()
        ),
        if_not_exists=True,
    )
    op.create_index(
        "ix_navigation_cache_node_slug",
        "navigation_cache",
        ["node_slug"],
        unique=True,
        if_not_exists=True,
    )


def downgrade() -> None:
    op.drop_index(
        "ix_navigation_cache_node_slug",
        table_name="navigation_cache",
        if_exists=True,
    )
    op.drop_table("navigation_cache", if_exists=True)

"""drop legacy node fields

Revision ID: 20251229_drop_legacy_node_fields
Revises: 20251228_drop_quest_step_content_refs
Create Date: 2025-12-29
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = "20251229_drop_legacy_node_fields"
down_revision = "20251228_drop_quest_step_content_refs"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.drop_index("ix_nodes_is_public", table_name="nodes")
    with op.batch_alter_table("nodes") as batch:
        batch.drop_column("content")
        batch.drop_column("reactions")
        batch.drop_column("is_public")
        batch.drop_column("cover_url")
        batch.drop_column("media")


def downgrade() -> None:
    with op.batch_alter_table("nodes") as batch:
        batch.add_column(sa.Column("media", postgresql.ARRAY(sa.String()), nullable=True))
        batch.add_column(sa.Column("cover_url", sa.String(), nullable=True))
        batch.add_column(sa.Column("is_public", sa.Boolean(), nullable=True))
        batch.add_column(sa.Column("reactions", postgresql.JSONB(astext_type=sa.Text()), nullable=True))
        batch.add_column(
            sa.Column(
                "content",
                postgresql.JSONB(astext_type=sa.Text()),
                nullable=False,
                server_default=sa.text("'{}'::jsonb"),
            )
        )
    op.create_index("ix_nodes_is_public", "nodes", ["is_public"])

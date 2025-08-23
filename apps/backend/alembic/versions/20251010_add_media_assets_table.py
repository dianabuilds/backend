"""create media_assets table

Revision ID: 20251010_add_media_assets_table
Revises: 20250920_add_tags_tables
Create Date: 2025-10-10
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = "20251010_add_media_assets_table"
down_revision = "20250920_add_tags_tables"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "media_assets",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("workspace_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("url", sa.String(), nullable=False),
        sa.Column("type", sa.String(), nullable=False),
        sa.Column(
            "metadata_json",
            postgresql.JSONB(astext_type=sa.Text()),
            nullable=True,
        ),
        sa.Column("created_at", sa.DateTime(), server_default=sa.func.now()),
        sa.ForeignKeyConstraint(["workspace_id"], ["workspaces.id"]),
    )
    op.create_index(
        "ix_media_assets_workspace",
        "media_assets",
        ["workspace_id"],
    )


def downgrade() -> None:
    op.drop_index("ix_media_assets_workspace", table_name="media_assets")
    op.drop_table("media_assets")

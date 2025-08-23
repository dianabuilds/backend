"""create content_items table

Revision ID: 20250915_01_create_content_items
Revises: 20250901_world_char_ws
Create Date: 2025-09-15
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


revision = "20250915_01_create_content_items"
down_revision = "20250901_world_char_ws"
branch_labels = None
depends_on = None

content_status = postgresql.ENUM(
    "draft",
    "in_review",
    "published",
    "archived",
    name="content_status",
    create_type=False,
)


def upgrade() -> None:
    bind = op.get_bind()
    existing = bind.execute(
        sa.text("SELECT 1 FROM pg_type WHERE typname = 'content_status'")
    ).scalar()
    if not existing:
        content_status.create(bind)

    op.create_table(
        "content_items",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("workspace_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("type", sa.String(), nullable=False),
        sa.Column("status", content_status, nullable=False, server_default="draft"),
        sa.Column("version", sa.Integer(), nullable=False, server_default="1"),
        sa.Column("slug", sa.String(), nullable=False),
        sa.Column("title", sa.String(), nullable=False),
        sa.Column("summary", sa.Text(), nullable=True),
        sa.Column("cover_media_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("primary_tag_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("created_by_user_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("updated_by_user_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("published_at", sa.DateTime(), nullable=True),
        sa.Column("created_at", sa.DateTime(), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(["workspace_id"], ["workspaces.id"]),
        sa.ForeignKeyConstraint(["primary_tag_id"], ["tags.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["created_by_user_id"], ["users.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["updated_by_user_id"], ["users.id"], ondelete="SET NULL"),
    )
    op.create_index("ix_content_items_slug", "content_items", ["slug"], unique=True)


def downgrade() -> None:
    op.drop_index("ix_content_items_slug", table_name="content_items")
    op.drop_table("content_items")

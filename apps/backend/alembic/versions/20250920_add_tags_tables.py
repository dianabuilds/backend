"""create tags and content_tags tables

Revision ID: 20250920_add_tags_tables
Revises: 20250915_01_create_content_items
Create Date: 2025-09-20
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy import inspect
from sqlalchemy.dialects import postgresql

revision = "20250920_add_tags_tables"
down_revision = "20250915_01_create_content_items"
branch_labels = None
depends_on = None


def upgrade() -> None:
    bind = op.get_bind()
    inspector = inspect(bind)

    if "tags" not in inspector.get_table_names():
        op.create_table(
            "tags",
            sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
            sa.Column("workspace_id", postgresql.UUID(as_uuid=True), nullable=False),
            sa.Column("slug", sa.String(), nullable=False),
            sa.Column("name", sa.String(), nullable=False),
            sa.Column(
                "created_at",
                sa.DateTime(),
                server_default=sa.func.now(),
                nullable=False,
            ),
            sa.Column(
                "is_hidden",
                sa.Boolean(),
                nullable=False,
                server_default=sa.text("false"),
            ),
            sa.ForeignKeyConstraint(["workspace_id"], ["workspaces.id"]),
            sa.UniqueConstraint("workspace_id", "slug", name="uq_tags_workspace_slug"),
        )

    tag_indexes = []
    if "tags" in inspector.get_table_names():
        tag_indexes = [idx["name"] for idx in inspector.get_indexes("tags")]
    if "ix_tags_slug" not in tag_indexes:
        op.create_index("ix_tags_slug", "tags", ["slug"])

    if "content_tags" not in inspector.get_table_names():
        op.create_table(
            "content_tags",
            sa.Column("content_id", postgresql.UUID(as_uuid=True), primary_key=True),
            sa.Column("tag_id", postgresql.UUID(as_uuid=True), primary_key=True),
            sa.Column("workspace_id", postgresql.UUID(as_uuid=True), nullable=False),
            sa.Column(
                "created_at",
                sa.DateTime(),
                server_default=sa.func.now(),
                nullable=False,
            ),
            sa.ForeignKeyConstraint(
                ["content_id"], ["content_items.id"], ondelete="CASCADE"
            ),
            sa.ForeignKeyConstraint(["tag_id"], ["tags.id"], ondelete="CASCADE"),
            sa.ForeignKeyConstraint(["workspace_id"], ["workspaces.id"]),
        )

    content_tag_indexes = []
    if "content_tags" in inspector.get_table_names():
        content_tag_indexes = [
            idx["name"] for idx in inspector.get_indexes("content_tags")
        ]
    if "ix_content_tags_content_id" not in content_tag_indexes:
        op.create_index("ix_content_tags_content_id", "content_tags", ["content_id"])
    if "ix_content_tags_tag_id" not in content_tag_indexes:
        op.create_index("ix_content_tags_tag_id", "content_tags", ["tag_id"])


def downgrade() -> None:
    bind = op.get_bind()
    inspector = inspect(bind)

    if "content_tags" in inspector.get_table_names():
        existing_indexes = [
            idx["name"] for idx in inspector.get_indexes("content_tags")
        ]
        if "ix_content_tags_tag_id" in existing_indexes:
            op.drop_index("ix_content_tags_tag_id", table_name="content_tags")
        if "ix_content_tags_content_id" in existing_indexes:
            op.drop_index("ix_content_tags_content_id", table_name="content_tags")
        op.drop_table("content_tags")

    if "tags" in inspector.get_table_names():
        existing_indexes = [idx["name"] for idx in inspector.get_indexes("tags")]
        if "ix_tags_slug" in existing_indexes:
            op.drop_index("ix_tags_slug", table_name="tags")
        op.drop_table("tags")

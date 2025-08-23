"""add workspace and status fields to content tables

Revision ID: 20250822_content_ws_status
Revises: 20250822_ws_members
Create Date: 2025-08-22
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = "20250822_content_ws_status"
down_revision = "20250822_ws_members"
branch_labels = None
depends_on = None

content_status = postgresql.ENUM("draft", "in_review", "published", "archived", name="content_status", create_type=False)
content_visibility = postgresql.ENUM("private", "unlisted", "public", name="content_visibility", create_type=False)

def upgrade() -> None:
    bind = op.get_bind()
    content_status.create(bind, checkfirst=True)
    content_visibility.create(bind, checkfirst=True)

    tables = ["quests", "nodes", "achievements", "notifications"]
    for table in tables:
        op.add_column(table, sa.Column("workspace_id", sa.dialects.postgresql.UUID(as_uuid=True), nullable=False))
        op.add_column(table, sa.Column("status", content_status, nullable=False, server_default="draft"))
        op.add_column(table, sa.Column("version", sa.Integer(), nullable=False, server_default="1"))
        op.add_column(table, sa.Column("visibility", content_visibility, nullable=False, server_default="private"))
        op.add_column(table, sa.Column("created_by_user_id", sa.dialects.postgresql.UUID(as_uuid=True), nullable=True))
        op.add_column(table, sa.Column("updated_by_user_id", sa.dialects.postgresql.UUID(as_uuid=True), nullable=True))

    # add foreign keys
    for table in tables:
        op.create_foreign_key(None, table, "workspaces", ["workspace_id"], ["id"])
        op.create_foreign_key(None, table, "users", ["created_by_user_id"], ["id"], ondelete="SET NULL")
        op.create_foreign_key(None, table, "users", ["updated_by_user_id"], ["id"], ondelete="SET NULL")

def downgrade() -> None:
    tables = ["quests", "nodes", "achievements", "notifications"]
    for table in tables:
        op.drop_column(table, "updated_by_user_id")
        op.drop_column(table, "created_by_user_id")
        op.drop_column(table, "visibility")
        op.drop_column(table, "version")
        op.drop_column(table, "status")
        op.drop_column(table, "workspace_id")

    bind = op.get_bind()
    content_visibility.drop(bind, checkfirst=True)
    content_status.drop(bind, checkfirst=True)

"""add workspace and status fields to world and character tables

Revision ID: 20250901_01_world_character_workspace
Revises: 20250822_02_content_workspace_and_status
Create Date: 2025-09-01
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = "20250901_01_world_character_workspace"
down_revision = "20250822_02_content_workspace_and_status"
branch_labels = None
depends_on = None

content_status = sa.Enum("draft", "in_review", "published", "archived", name="content_status")
content_visibility = sa.Enum("private", "unlisted", "public", name="content_visibility")


def upgrade() -> None:
    bind = op.get_bind()
    content_status.create(bind, checkfirst=True)
    content_visibility.create(bind, checkfirst=True)

    for table in ["world_templates", "characters"]:
        op.add_column(table, sa.Column("workspace_id", postgresql.UUID(as_uuid=True), nullable=True))
        op.add_column(table, sa.Column("status", content_status, nullable=False, server_default="draft"))
        op.add_column(table, sa.Column("version", sa.Integer(), nullable=False, server_default="1"))
        op.add_column(table, sa.Column("visibility", content_visibility, nullable=False, server_default="private"))
        op.add_column(table, sa.Column("created_by_user_id", postgresql.UUID(as_uuid=True), nullable=True))
        op.add_column(table, sa.Column("updated_by_user_id", postgresql.UUID(as_uuid=True), nullable=True))
        op.create_foreign_key(None, table, "workspaces", ["workspace_id"], ["id"])
        op.create_foreign_key(None, table, "users", ["created_by_user_id"], ["id"], ondelete="SET NULL")
        op.create_foreign_key(None, table, "users", ["updated_by_user_id"], ["id"], ondelete="SET NULL")

    workspace_id = bind.execute(sa.text("SELECT id FROM workspaces LIMIT 1")).scalar()
    if workspace_id:
        bind.execute(sa.text("UPDATE world_templates SET workspace_id = :id WHERE workspace_id IS NULL"), {"id": workspace_id})
        bind.execute(sa.text("""
            UPDATE characters AS c
            SET workspace_id = wt.workspace_id
            FROM world_templates AS wt
            WHERE c.world_id = wt.id AND c.workspace_id IS NULL
        """))
        op.alter_column("world_templates", "workspace_id", nullable=False)
        op.alter_column("characters", "workspace_id", nullable=False)


def downgrade() -> None:
    for table in ["characters", "world_templates"]:
        op.drop_column(table, "updated_by_user_id")
        op.drop_column(table, "created_by_user_id")
        op.drop_column(table, "visibility")
        op.drop_column(table, "version")
        op.drop_column(table, "status")
        op.drop_column(table, "workspace_id")

    content_visibility.drop(op.get_bind(), checkfirst=True)
    content_status.drop(op.get_bind(), checkfirst=True)

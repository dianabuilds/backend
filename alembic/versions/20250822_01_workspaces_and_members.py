"""workspaces + workspace_members

Revision ID: 20250822_01
Revises:
Create Date: 2025-08-22

"""
from __future__ import annotations

import uuid
from typing import Optional

from alembic import op
import sqlalchemy as sa
from sqlalchemy import text
from sqlalchemy.engine.reflection import Inspector

# revision identifiers, used by Alembic.
revision = "20250822_01"
down_revision: Optional[str] = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    # users.id должен существовать (UUID). Если у тебя другая схема – поправь FK ниже.
    op.create_table(
        "workspaces",
        sa.Column("id", sa.UUID(), primary_key=True, nullable=False),
        sa.Column("name", sa.String(length=200), nullable=False),
        sa.Column("slug", sa.String(length=200), nullable=False, unique=True),
        sa.Column("owner_user_id", sa.UUID(), nullable=True),
        sa.Column("settings_json", sa.JSON(), nullable=False, server_default=sa.text("'{}'::json")),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["owner_user_id"], ["users.id"], name="fk_workspaces_owner_user", ondelete="SET NULL"),
    )
    op.create_index("ix_workspaces_slug", "workspaces", ["slug"], unique=True)

    # roles: owner | editor | viewer
    roles_enum = sa.Enum("owner", "editor", "viewer", name="workspace_role")
    roles_enum.create(op.get_bind(), checkfirst=True)

    op.create_table(
        "workspace_members",
        sa.Column("workspace_id", sa.UUID(), nullable=False),
        sa.Column("user_id", sa.UUID(), nullable=False),
        sa.Column("role", roles_enum, nullable=False, server_default="editor"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["workspace_id"], ["workspaces.id"], name="fk_workspace_members_ws", ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], name="fk_workspace_members_user", ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("workspace_id", "user_id", name="pk_workspace_members"),
    )

    # Создадим "Default" workspace, чтобы на следующем шаге было куда привязать существующий контент.
    conn = op.get_bind()
    default_ws_id = str(uuid.uuid4())
    conn.execute(
        text(
            "INSERT INTO workspaces (id, name, slug, settings_json) "
            "VALUES (:id, :name, :slug, '{}'::json)"
        ),
        {"id": default_ws_id, "name": "Default", "slug": "default"},
    )

    # Если есть админ-пользователь — добавим его owner’ом (не строго обязательно)
    # Попробуем найти первого is_admin=true, если такое поле у тебя есть.
    try:
        res = conn.execute(text("SELECT id FROM users WHERE is_admin = true LIMIT 1")).first()
        if res:
            admin_id = res[0]
            conn.execute(
                text(
                    "INSERT INTO workspace_members (workspace_id, user_id, role) "
                    "VALUES (:ws, :uid, 'owner') ON CONFLICT DO NOTHING"
                ),
                {"ws": default_ws_id, "uid": admin_id},
            )
    except Exception:
        # если нет поля is_admin — просто пропустим
        pass


def downgrade() -> None:
    conn = op.get_bind()
    # Drop members first
    op.drop_table("workspace_members")
    # Drop role enum
    try:
        sa.Enum(name="workspace_role").drop(conn, checkfirst=True)
    except Exception:
        pass
    # Drop workspaces
    op.drop_index("ix_workspaces_slug", table_name="workspaces")
    op.drop_table("workspaces")

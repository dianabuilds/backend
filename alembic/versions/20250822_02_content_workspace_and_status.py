"""attach content to workspaces + status/version/visibility

Revision ID: 20250822_02
Revises: 20250822_01
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
revision = "20250822_02"
down_revision: Optional[str] = "20250822_01"
branch_labels = None
depends_on = None

CONTENT_TABLES_CANDIDATES = [
    # подставь реальные имена таблиц, которые у тебя уже есть
    "quests",
    "worlds",
    "nodes",
    "achievements",
    # "blog_posts",      # раскомментируй, когда появится блог
    # "characters",      # если у тебя есть персонажи отдельной таблицей
]

STATUS_ENUM = sa.Enum("draft", "in_review", "published", "archived", name="content_status")
VIS_ENUM = sa.Enum("private", "unlisted", "public", name="content_visibility")


def _has_table(inspector: Inspector, name: str) -> bool:
    try:
        return name in inspector.get_table_names()
    except Exception:
        return False


def upgrade() -> None:
    bind = op.get_bind()
    insp = sa.inspect(bind)

    # Создадим enum’ы один раз
    STATUS_ENUM.create(bind, checkfirst=True)
    VIS_ENUM.create(bind, checkfirst=True)

    # Возьмём какой-нибудь workspace (Default из первой миграции)
    ws = bind.execute(text("SELECT id FROM workspaces ORDER BY created_at ASC LIMIT 1")).first()
    default_ws_id = ws[0] if ws else str(uuid.uuid4())

    if not ws:
        # крайне маловероятно, но на всякий случай
        bind.execute(
            text("INSERT INTO workspaces (id, name, slug, settings_json) VALUES (:id,'Default','default','{}'::json)"),
            {"id": default_ws_id},
        )

    for table in CONTENT_TABLES_CANDIDATES:
        if not _has_table(insp, table):
            continue

        # 1) Добавляем колонки с IF NOT EXISTS (для Postgres)
        op.execute(sa.text(f'ALTER TABLE "{table}" ADD COLUMN IF NOT EXISTS workspace_id uuid'))
        op.execute(sa.text(f'ALTER TABLE "{table}" ADD COLUMN IF NOT EXISTS status content_status DEFAULT \'draft\' NOT NULL'))
        op.execute(sa.text(f'ALTER TABLE "{table}" ADD COLUMN IF NOT EXISTS version integer DEFAULT 1 NOT NULL'))
        op.execute(sa.text(f'ALTER TABLE "{table}" ADD COLUMN IF NOT EXISTS visibility content_visibility DEFAULT \'private\' NOT NULL'))
        op.execute(sa.text(f'ALTER TABLE "{table}" ADD COLUMN IF NOT EXISTS created_by_user_id uuid'))
        op.execute(sa.text(f'ALTER TABLE "{table}" ADD COLUMN IF NOT EXISTS updated_by_user_id uuid'))

        # 2) FK + индексы
        # FK на workspace
        op.execute(sa.text(
            f'ALTER TABLE "{table}" '
            'ADD CONSTRAINT IF NOT EXISTS '
            f'fk_{table}_workspace FOREIGN KEY (workspace_id) REFERENCES workspaces(id) ON DELETE RESTRICT'
        ))
        # FK на users (если нужно отслеживать авторов)
        op.execute(sa.text(
            f'ALTER TABLE "{table}" '
            'ADD CONSTRAINT IF NOT EXISTS '
            f'fk_{table}_created_by FOREIGN KEY (created_by_user_id) REFERENCES users(id) ON DELETE SET NULL'
        ))
        op.execute(sa.text(
            f'ALTER TABLE "{table}" '
            'ADD CONSTRAINT IF NOT EXISTS '
            f'fk_{table}_updated_by FOREIGN KEY (updated_by_user_id) REFERENCES users(id) ON DELETE SET NULL'
        ))

        op.execute(sa.text(f'CREATE INDEX IF NOT EXISTS ix_{table}_workspace ON "{table}" (workspace_id)'))
        op.execute(sa.text(f'CREATE INDEX IF NOT EXISTS ix_{table}_status ON "{table}" (status)'))
        op.execute(sa.text(f'CREATE INDEX IF NOT EXISTS ix_{table}_visibility ON "{table}" (visibility)'))

        # 3) Бэкфилл существующих строк в default workspace
        op.execute(sa.text(f'UPDATE "{table}" SET workspace_id = :ws WHERE workspace_id IS NULL'), {"ws": default_ws_id})

        # 4) Сделаем NOT NULL после бэкфилла
        op.execute(sa.text(f'ALTER TABLE "{table}" ALTER COLUMN workspace_id SET NOT NULL'))

    # Примечание по тегам:
    # Если захочешь сделать теги «по workspace», добавим workspace_id в tags и UNIQUE(workspace_id, slug) отдельной миграцией,
    # чтобы не трогать существующие уникальные ограничения на slug.


def downgrade() -> None:
    bind = op.get_bind()
    insp = sa.inspect(bind)

    for table in CONTENT_TABLES_CANDIDATES:
        if not _has_table(insp, table):
            continue
        # снимем ограничения/индексы и удалим колонки
        op.execute(sa.text(f'DROP INDEX IF EXISTS ix_{table}_workspace'))
        op.execute(sa.text(f'DROP INDEX IF EXISTS ix_{table}_status'))
        op.execute(sa.text(f'DROP INDEX IF EXISTS ix_{table}_visibility'))

        op.execute(sa.text(f'ALTER TABLE "{table}" DROP CONSTRAINT IF EXISTS fk_{table}_workspace'))
        op.execute(sa.text(f'ALTER TABLE "{table}" DROP CONSTRAINT IF EXISTS fk_{table}_created_by'))
        op.execute(sa.text(f'ALTER TABLE "{table}" DROP CONSTRAINT IF EXISTS fk_{table}_updated_by'))

        for col in ["visibility", "version", "status", "updated_by_user_id", "created_by_user_id", "workspace_id"]:
            op.execute(sa.text(f'ALTER TABLE "{table}" DROP COLUMN IF EXISTS {col}'))

    # enums
    try:
        VIS_ENUM.drop(bind, checkfirst=True)
    except Exception:
        pass
    try:
        STATUS_ENUM.drop(bind, checkfirst=True)
    except Exception:
        pass

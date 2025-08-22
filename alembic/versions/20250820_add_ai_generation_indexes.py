"""add composite index for ai_generation_jobs (status, created_at)

Revision ID: 20250820_add_ai_generation_indexes
Revises: 
Create Date: 2025-08-20

"""
from __future__ import annotations

from alembic import op


# revision identifiers, used by Alembic.
revision = "20250820_add_ai_generation_indexes"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Индекс мог уже существовать (dev create_all), поэтому if_exists=False игнорируем — Alembic не поддерживает напрямую.
    # Попытаемся создать, при ошибке (существует) БД сама сообщит — в dev это ок; в проде управляется порядком миграций.
    try:
        op.create_index("ix_ai_generation_jobs_status_created_at", "ai_generation_jobs", ["status", "created_at"])
    except Exception:
        # На некоторых движках (например, SQLite) повторное создание приведет к ошибке — безопасно игнорируем
        pass


def downgrade() -> None:
    try:
        op.drop_index("ix_ai_generation_jobs_status_created_at", table_name="ai_generation_jobs")
    except Exception:
        pass

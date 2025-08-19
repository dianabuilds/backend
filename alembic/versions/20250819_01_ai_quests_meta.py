"""AI quests: quest generation metadata and ai_generation_jobs

Revision ID: 20250819_01_ai_quests_meta
Revises:
Create Date: 2025-08-19 00:00:00

"""
from __future__ import annotations

from alembic import op
import sqlalchemy as sa
from sqlalchemy.engine.reflection import Inspector

# revision identifiers, used by Alembic.
revision = "20250819_01_ai_quests_meta"
down_revision = "20250905_add_cover_url"
branch_labels = None
depends_on = None


def _get_inspector(bind) -> Inspector:
    try:
        return sa.inspect(bind)
    except Exception:
        return Inspector.from_engine(bind)


def _has_table(inspector: Inspector, table_name: str) -> bool:
    try:
        return table_name in inspector.get_table_names()
    except Exception:
        # fallback: attempt select
        return False


def _has_column(inspector: Inspector, table_name: str, column_name: str) -> bool:
    try:
        cols = [c["name"] for c in inspector.get_columns(table_name)]
        return column_name in cols
    except Exception:
        return False


def upgrade():
    bind = op.get_bind()
    insp = _get_inspector(bind)

    # 1) quests: добавить метаданные генерации
    if _has_table(insp, "quests"):
        if not _has_column(insp, "quests", "structure"):
            op.add_column("quests", sa.Column("structure", sa.String(), nullable=True))
        if not _has_column(insp, "quests", "length"):
            op.add_column("quests", sa.Column("length", sa.String(), nullable=True))
        if not _has_column(insp, "quests", "tone"):
            op.add_column("quests", sa.Column("tone", sa.String(), nullable=True))
        if not _has_column(insp, "quests", "genre"):
            op.add_column("quests", sa.Column("genre", sa.String(), nullable=True))
        if not _has_column(insp, "quests", "locale"):
            op.add_column("quests", sa.Column("locale", sa.String(), nullable=True))
        if not _has_column(insp, "quests", "cost_generation"):
            op.add_column("quests", sa.Column("cost_generation", sa.Integer(), nullable=True))

    # 2) ai_generation_jobs: создать или дополнить
    if not _has_table(insp, "ai_generation_jobs"):
        op.create_table(
            "ai_generation_jobs",
            sa.Column("id", sa.dialects.postgresql.UUID(as_uuid=True), primary_key=True),
            sa.Column("created_by", sa.dialects.postgresql.UUID(as_uuid=True), nullable=True),
            sa.Column("provider", sa.String(), nullable=True),
            sa.Column("model", sa.String(), nullable=True),
            sa.Column("params", sa.JSON(), nullable=False),
            sa.Column("status", sa.String(), nullable=False, index=True),
            sa.Column("created_at", sa.DateTime(), nullable=False, server_default=sa.func.now()),
            sa.Column("started_at", sa.DateTime(), nullable=True),
            sa.Column("finished_at", sa.DateTime(), nullable=True),
            sa.Column("result_quest_id", sa.dialects.postgresql.UUID(as_uuid=True), nullable=True),
            sa.Column("result_version_id", sa.dialects.postgresql.UUID(as_uuid=True), nullable=True),
            sa.Column("cost", sa.Float(), nullable=True),
            sa.Column("token_usage", sa.JSON(), nullable=True),
            sa.Column("reused", sa.Boolean(), nullable=False, server_default=sa.false()),
            sa.Column("progress", sa.Integer(), nullable=False, server_default="0"),
            sa.Column("logs", sa.JSON(), nullable=True),
            sa.Column("error", sa.Text(), nullable=True),
        )
    else:
        # добавить недостающие столбцы
        if not _has_column(insp, "ai_generation_jobs", "reused"):
            op.add_column("ai_generation_jobs", sa.Column("reused", sa.Boolean(), nullable=False, server_default=sa.false()))
        if not _has_column(insp, "ai_generation_jobs", "progress"):
            op.add_column("ai_generation_jobs", sa.Column("progress", sa.Integer(), nullable=False, server_default="0"))
        if not _has_column(insp, "ai_generation_jobs", "logs"):
            op.add_column("ai_generation_jobs", sa.Column("logs", sa.JSON(), nullable=True))


def downgrade():
    bind = op.get_bind()
    insp = _get_inspector(bind)

    # Откат полей в quests
    if _has_table(insp, "quests"):
        for col in ["cost_generation", "locale", "genre", "tone", "length", "structure"]:
            if _has_column(insp, "quests", col):
                op.drop_column("quests", col)

    # Откат таблицы ai_generation_jobs (если нужно)
    if _has_table(insp, "ai_generation_jobs"):
        # Можно удалить всю таблицу. Если важны данные, лучше не удалять.
        op.drop_table("ai_generation_jobs")

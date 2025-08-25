"""ensure tags.workspace_id exists and is indexed"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy import inspect
from sqlalchemy.dialects import postgresql

revision = "20251212_add_workspace_id_to_tags"
down_revision = "20251211_add_workspace_id_outbox"
branch_labels = None
depends_on = None


def upgrade() -> None:
    bind = op.get_bind()
    inspector = inspect(bind)

    table = "tags"
    if table in inspector.get_table_names():
        cols = {c["name"] for c in inspector.get_columns(table)}
        # 1) Добавляем колонку при отсутствии
        if "workspace_id" not in cols:
            op.add_column(
                table,
                sa.Column("workspace_id", postgresql.UUID(as_uuid=True), nullable=True),
            )

        # 2) Убедимся, что есть внешний ключ (если нет — создадим)
        fks = {fk["name"] for fk in inspector.get_foreign_keys(table)}
        if "fk_tags_workspace_id" not in fks:
            op.create_foreign_key(
                "fk_tags_workspace_id", table, "workspaces", ["workspace_id"], ["id"]
            )

        # 3) Проставим workspace_id для строк с NULL
        #    Пытаемся взять id рабочей области со slug='main', если нет — любой существующий workspace
        wid = bind.execute(
            sa.text("SELECT id FROM workspaces WHERE slug='main' LIMIT 1")
        ).scalar()
        if wid is None:
            wid = bind.execute(sa.text("SELECT id FROM workspaces LIMIT 1")).scalar()

        if wid is not None:
            op.execute(
                sa.text(
                    "UPDATE tags SET workspace_id = :wid WHERE workspace_id IS NULL"
                ).bindparams(wid=wid)
            )
        # 4) Если NULL больше не осталось — делаем колонку NOT NULL
        nulls = bind.execute(
            sa.text("SELECT COUNT(*) FROM tags WHERE workspace_id IS NULL")
        ).scalar()
        if nulls == 0:
            op.alter_column(table, "workspace_id", nullable=False)

        # 5) Индекс
        indexes = {idx["name"] for idx in inspector.get_indexes(table)}
        if "ix_tags_workspace_id" not in indexes:
            op.create_index("ix_tags_workspace_id", table, ["workspace_id"])

        # 6) Уникальные ограничения: удалим старое по slug и создадим составное
        constraints = {c["name"] for c in inspector.get_unique_constraints(table)}
        if "uq_tags_slug" in constraints:
            op.drop_constraint("uq_tags_slug", table_name=table, type_="unique")
        if "uq_tags_workspace_slug" not in constraints:
            op.create_unique_constraint(
                "uq_tags_workspace_slug", table, ["workspace_id", "slug"]
            )


def downgrade() -> None:
    bind = op.get_bind()
    inspector = inspect(bind)

    table = "tags"
    if table in inspector.get_table_names():
        constraints = {c["name"] for c in inspector.get_unique_constraints(table)}
        if "uq_tags_workspace_slug" in constraints:
            op.drop_constraint(
                "uq_tags_workspace_slug", table_name=table, type_="unique"
            )
        indexes = {idx["name"] for idx in inspector.get_indexes(table)}
        if "ix_tags_workspace_id" in indexes:
            op.drop_index("ix_tags_workspace_id", table_name=table)
        fks = {fk["name"] for fk in inspector.get_foreign_keys(table)}
        if "fk_tags_workspace_id" in fks:
            op.drop_constraint(
                "fk_tags_workspace_id", table_name=table, type_="foreignkey"
            )
        cols = {c["name"] for c in inspector.get_columns(table)}
        if "workspace_id" in cols:
            op.drop_column(table, "workspace_id")

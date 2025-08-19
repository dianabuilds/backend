from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = "20250813_drop_content_format"
down_revision = "a3f9d2b1b1a3"
branch_labels = None
depends_on = None


def _table_exists(table_name: str) -> bool:
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    return table_name in inspector.get_table_names()


def _column_exists(table_name: str, column_name: str) -> bool:
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    cols = [c["name"] for c in inspector.get_columns(table_name)]
    return column_name in cols


def upgrade():
    if _table_exists("nodes") and _column_exists("nodes", "content_format"):
        try:
            op.drop_column("nodes", "content_format")
        except Exception:
            # если колонка чем-то зависима — оставим ручной разбор
            pass
    # Пытаемся удалить тип enum, если он существовал
    bind = op.get_bind()
    if bind.dialect.name == "postgresql":
        try:
            op.execute("DROP TYPE IF EXISTS contentformat")
        except Exception:
            # если тип используется где-то еще — пропускаем
            pass


def downgrade():
    # Downgrade опционален; если потребуется — можно вернуть тип и колонку
    bind = op.get_bind()
    if bind.dialect.name == "postgresql":
        try:
            op.execute("CREATE TYPE contentformat AS ENUM ('rich_json')")
        except Exception:
            pass
    if _table_exists("nodes") and not _column_exists("nodes", "content_format"):
        try:
            op.add_column(
                "nodes",
                sa.Column("content_format", sa.Enum(name="contentformat"), nullable=True),
            )
        except Exception:
            pass

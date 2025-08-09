from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = 'a3f9d2b1b1a3'
down_revision = '7f2b8e536ab1'
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
    # Ничего не делаем, если таблицы users нет (на чистой БД её создаст create_all/первая миграция)
    if not _table_exists("users"):
        return

    # Добавляем users.is_premium (BOOLEAN NOT NULL DEFAULT false), если отсутствует
    if not _column_exists("users", "is_premium"):
        op.add_column(
            "users",
            sa.Column("is_premium", sa.Boolean(), nullable=False, server_default=sa.false()),
        )
        # не выполняем лишний alter_column для снятия server_default — это безопасно оставить

    # Добавляем users.premium_until (TIMESTAMP NULL), если отсутствует
    if not _column_exists("users", "premium_until"):
        op.add_column("users", sa.Column("premium_until", sa.DateTime(), nullable=True))


def downgrade():
    if not _table_exists("users"):
        return

    # Откатываем в обратном порядке при наличии колонок
    if _column_exists("users", "premium_until"):
        op.drop_column("users", "premium_until")
    if _column_exists("users", "is_premium"):
        op.drop_column("users", "is_premium")

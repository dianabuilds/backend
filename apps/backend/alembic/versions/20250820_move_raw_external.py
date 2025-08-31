from alembic import op
import sqlalchemy as sa
from sqlalchemy import text

# revision identifiers, used by Alembic.
revision = "20250820_move_raw_external"
down_revision = "20250820_worlds_chars_ai"
branch_labels = None
depends_on = None

TRUNCATE_LEN = 16384  # должен соответствовать RAW_LOG_MAX_DB по умолчанию


def upgrade():
    # Добавляем новые колонки
    op.add_column("generation_job_logs", sa.Column("raw_url", sa.Text(), nullable=True))
    op.add_column(
        "generation_job_logs", sa.Column("raw_preview", sa.Text(), nullable=True)
    )

    # Заполняем raw_preview усечённой копией raw_response для уже существующих записей
    bind = op.get_bind()
    dialect = bind.dialect.name
    try:
        if dialect == "postgresql":
            bind.execute(
                text(
                    "UPDATE generation_job_logs "
                    "SET raw_preview = LEFT(raw_response, :n) "
                    "WHERE raw_preview IS NULL AND raw_response IS NOT NULL"
                ).bindparams(n=TRUNCATE_LEN)
            )
        else:
            bind.execute(
                text(
                    "UPDATE generation_job_logs "
                    "SET raw_preview = substr(raw_response, 1, :n) "
                    "WHERE raw_preview IS NULL AND raw_response IS NOT NULL"
                ).bindparams(n=TRUNCATE_LEN)
            )
    except Exception:
        # Если что-то пошло не так на экзотическом диалекте — просто оставим пустым
        pass


def downgrade():
    op.drop_column("generation_job_logs", "raw_preview")
    op.drop_column("generation_job_logs", "raw_url")

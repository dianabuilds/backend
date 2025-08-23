from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = "20250905_add_cover_url"
down_revision = "20250813_drop_content_format"
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
    if _table_exists("nodes") and not _column_exists("nodes", "cover_url"):
        op.add_column("nodes", sa.Column("cover_url", sa.Text(), nullable=True))


def downgrade():
    if _table_exists("nodes") and _column_exists("nodes", "cover_url"):
        op.drop_column("nodes", "cover_url")

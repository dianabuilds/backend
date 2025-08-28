from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = "20251219_drop_quest_data_from_content_items"
down_revision = "20251218_add_node_id_fk"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.drop_column("content_items", "quest_data")


def downgrade() -> None:
    op.add_column(
        "content_items",
        sa.Column("quest_data", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
    )

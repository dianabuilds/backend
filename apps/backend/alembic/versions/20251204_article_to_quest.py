from alembic import op
import sqlalchemy as sa

revision = "20251204_article_to_quest"
down_revision = "20251203_quests_workspace_idx"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute(sa.text("UPDATE content_items SET type='quest' WHERE type='article'"))


def downgrade() -> None:
    op.execute(sa.text("UPDATE content_items SET type='article' WHERE type='quest'"))

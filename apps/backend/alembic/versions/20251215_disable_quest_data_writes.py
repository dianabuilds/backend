from alembic import op

revision = "20251215_disable_quest_data_writes"
down_revision = "20251214_create_quest_tables"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute(
        "ALTER TABLE content_items ADD CONSTRAINT content_items_quest_data_is_null CHECK (quest_data IS NULL) NOT VALID"
    )


def downgrade() -> None:
    op.execute(
        "ALTER TABLE content_items DROP CONSTRAINT IF EXISTS content_items_quest_data_is_null"
    )

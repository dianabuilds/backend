"""merge alembic heads"""

revision = "20251217_merge_heads"
down_revision = (
    "20251216_add_navigation_cache_table",
    "20251215_disable_quest_data_writes",
)
branch_labels = None
depends_on = None


def upgrade() -> None:
    pass


def downgrade() -> None:
    pass

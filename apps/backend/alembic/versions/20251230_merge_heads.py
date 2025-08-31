"""merge alembic heads"""

revision = "20251230_merge_heads"
down_revision = ("20251229_drop_legacy_node_fields", "20251204_article_to_quest")
branch_labels = None
depends_on = None


def upgrade() -> None:
    pass


def downgrade() -> None:
    pass

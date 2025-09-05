from __future__ import annotations

from alembic import op

revision = "20260122_remove_moderation_flag"
down_revision = "20260121_add_feature_flag_audience"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute("DELETE FROM feature_flags WHERE key='moderation.enabled'")


def downgrade() -> None:
    op.execute(
        """
        INSERT INTO feature_flags (key, value, description, audience, updated_at)
        VALUES ('moderation.enabled', FALSE, 'Enable moderation section in admin UI', 'all', now())
        """
    )

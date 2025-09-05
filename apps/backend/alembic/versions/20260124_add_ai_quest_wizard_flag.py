from __future__ import annotations

from alembic import op

revision = "20260124_add_ai_quest_wizard_flag"
down_revision = "20260123_add_referrals_program_flag"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute(
        """
        INSERT INTO feature_flags (key, value, description, audience, updated_at)
        VALUES ('ai.quest_wizard', FALSE, 'Enable AI Quest Wizard', 'premium', now())
        ON CONFLICT (key) DO NOTHING
        """
    )


def downgrade() -> None:
    op.execute("DELETE FROM feature_flags WHERE key='ai.quest_wizard'")

from __future__ import annotations

from alembic import op

revision = "20260123_add_referrals_program_flag"
down_revision = "20260122_make_notifications_workspace_nullable"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute(
        """
        INSERT INTO feature_flags (key, value, description, audience, updated_at)
        VALUES ('referrals.program', FALSE, 'Enable referrals program', 'all', now())
        ON CONFLICT (key) DO NOTHING
        """
    )


def downgrade() -> None:
    op.execute("DELETE FROM feature_flags WHERE key='referrals.program'")

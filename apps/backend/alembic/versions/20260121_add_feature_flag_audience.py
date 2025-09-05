"""add audience column to feature_flags"""

from __future__ import annotations

from alembic import op
import sqlalchemy as sa

revision = "20260121_add_feature_flag_audience"
down_revision = "20260120_create_moderation_tables"
branch_labels = None
depends_on = None

feature_flag_audience = sa.Enum("all", "premium", "beta", name="feature_flag_audience")


def upgrade() -> None:
    feature_flag_audience.create(op.get_bind(), checkfirst=True)
    op.add_column(
        "feature_flags",
        sa.Column(
            "audience", feature_flag_audience, nullable=False, server_default="all"
        ),
    )
    op.execute("UPDATE feature_flags SET audience='all' WHERE audience IS NULL")


def downgrade() -> None:
    op.drop_column("feature_flags", "audience")
    feature_flag_audience.drop(op.get_bind(), checkfirst=True)

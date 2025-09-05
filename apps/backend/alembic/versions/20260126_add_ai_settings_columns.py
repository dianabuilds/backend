from __future__ import annotations

import sqlalchemy as sa
from alembic import op

revision = "20260126_add_ai_settings_columns"
down_revision = "20260125_ai_settings_int_id"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("ai_settings", sa.Column("model_map", sa.JSON(), nullable=True))
    op.add_column("ai_settings", sa.Column("cb", sa.JSON(), nullable=True))
    op.add_column(
        "ai_settings",
        sa.Column(
            "has_api_key", sa.Boolean(), nullable=False, server_default=sa.false()
        ),
    )
    op.execute(
        sa.text("UPDATE ai_settings SET has_api_key = TRUE WHERE api_key IS NOT NULL")
    )


def downgrade() -> None:
    op.drop_column("ai_settings", "has_api_key")
    op.drop_column("ai_settings", "cb")
    op.drop_column("ai_settings", "model_map")

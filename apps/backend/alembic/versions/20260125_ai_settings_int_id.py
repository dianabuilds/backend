from __future__ import annotations

import sqlalchemy as sa
from alembic import op

revision = "20260125_ai_settings_int_id"
down_revision = "20260124_add_ai_quest_wizard_flag"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.alter_column(
        "ai_settings",
        "id",
        type_=sa.Integer(),
        postgresql_using="id::integer",
    )


def downgrade() -> None:
    op.alter_column(
        "ai_settings",
        "id",
        type_=sa.dialects.postgresql.UUID(as_uuid=True),
        postgresql_using="id::uuid",
    )

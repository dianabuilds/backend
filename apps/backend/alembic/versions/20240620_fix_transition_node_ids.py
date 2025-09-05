from __future__ import annotations

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = "20240620_fix_transition_node_ids"
down_revision = "20260126_add_ai_settings_columns"
branch_labels = None
depends_on = None


def upgrade() -> None:
    with op.batch_alter_table("node_transitions") as batch:
        batch.alter_column(
            "from_node_id",
            type_=sa.BigInteger(),
            existing_type=postgresql.UUID(as_uuid=True),
            postgresql_using="from_node_id::text::bigint",
            existing_nullable=False,
        )
        batch.alter_column(
            "to_node_id",
            type_=sa.BigInteger(),
            existing_type=postgresql.UUID(as_uuid=True),
            postgresql_using="to_node_id::text::bigint",
            existing_nullable=False,
        )


def downgrade() -> None:
    with op.batch_alter_table("node_transitions") as batch:
        batch.alter_column(
            "from_node_id",
            type_=postgresql.UUID(as_uuid=True),
            existing_type=sa.BigInteger(),
            postgresql_using="from_node_id::text::uuid",
            existing_nullable=False,
        )
        batch.alter_column(
            "to_node_id",
            type_=postgresql.UUID(as_uuid=True),
            existing_type=sa.BigInteger(),
            postgresql_using="to_node_id::text::uuid",
            existing_nullable=False,
        )

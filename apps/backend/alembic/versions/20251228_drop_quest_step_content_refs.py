"""drop quest_step_content_refs and node fk columns"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


revision = "20251228_drop_quest_step_content_refs"
down_revision = "20251227_create_quest_steps_and_transitions"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.drop_table("quest_step_content_refs", if_exists=True)
    for table in ["quests", "quest_versions", "quest_steps", "quest_transitions"]:
        op.execute(f"ALTER TABLE {table} DROP COLUMN IF EXISTS node_id")
        op.execute(f"ALTER TABLE {table} DROP COLUMN IF EXISTS node_uuid")


def downgrade() -> None:
    for table in ["quests", "quest_versions", "quest_steps", "quest_transitions"]:
        op.add_column(
            table,
            sa.Column("node_id", postgresql.UUID(as_uuid=True), nullable=True),
        )
        op.add_column(
            table,
            sa.Column("node_uuid", postgresql.UUID(as_uuid=True), nullable=True),
        )

    op.create_table(
        "quest_step_content_refs",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("step_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("content_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("position", sa.Integer(), nullable=False, server_default="0"),
        sa.ForeignKeyConstraint(["step_id"], ["quest_steps.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["content_id"], ["nodes.alt_id"], ondelete="CASCADE"),
        sa.UniqueConstraint("step_id", "content_id", name="uq_step_content_ref"),
    )
    op.create_index(
        "ix_quest_step_content_refs_step_id",
        "quest_step_content_refs",
        ["step_id"],
    )
    op.create_index(
        "ix_quest_step_content_refs_content_id",
        "quest_step_content_refs",
        ["content_id"],
    )

"""create quest_steps and quest_step_transitions

Revision ID: 20251227_create_quest_steps_and_transitions
Revises: 20251226_convert_content_items_node_id
Create Date: 2025-12-27
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


revision = "20251227_create_quest_steps_and_transitions"
down_revision = "20251226_convert_content_items_node_id"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "quest_steps",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("version_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("key", sa.String(), nullable=False),
        sa.Column("title", sa.String(), nullable=False),
        sa.Column("type", sa.String(), nullable=False, server_default="normal"),
        sa.Column("content", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column("rewards", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(),
            nullable=False,
            server_default=sa.func.now(),
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(),
            nullable=False,
            server_default=sa.func.now(),
            server_onupdate=sa.func.now(),
        ),
        sa.ForeignKeyConstraint([
            "version_id"
        ], ["quest_versions.id"], ondelete="CASCADE"),
        sa.UniqueConstraint("version_id", "key", name="uq_quest_step_key"),
        if_not_exists=True,
    )
    op.create_index(
        "ix_quest_steps_version_id",
        "quest_steps",
        ["version_id"],
        if_not_exists=True,
    )

    op.create_table(
        "quest_step_transitions",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("version_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("from_step_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("to_step_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("label", sa.String(), nullable=True),
        sa.Column("condition", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.ForeignKeyConstraint([
            "version_id"
        ], ["quest_versions.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint([
            "from_step_id"
        ], ["quest_steps.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint([
            "to_step_id"
        ], ["quest_steps.id"], ondelete="CASCADE"),
        if_not_exists=True,
    )
    op.create_index(
        "ix_quest_step_transitions_version_id",
        "quest_step_transitions",
        ["version_id"],
        if_not_exists=True,
    )
    op.create_index(
        "ix_quest_step_transitions_from_step_id",
        "quest_step_transitions",
        ["from_step_id"],
        if_not_exists=True,
    )
    op.create_index(
        "ix_quest_step_transitions_to_step_id",
        "quest_step_transitions",
        ["to_step_id"],
        if_not_exists=True,
    )


def downgrade() -> None:
    op.drop_index(
        "ix_quest_step_transitions_to_step_id",
        table_name="quest_step_transitions",
        if_exists=True,
    )
    op.drop_index(
        "ix_quest_step_transitions_from_step_id",
        table_name="quest_step_transitions",
        if_exists=True,
    )
    op.drop_index(
        "ix_quest_step_transitions_version_id",
        table_name="quest_step_transitions",
        if_exists=True,
    )
    op.drop_table("quest_step_transitions", if_exists=True)

    op.drop_index(
        "ix_quest_steps_version_id",
        table_name="quest_steps",
        if_exists=True,
    )
    op.drop_table("quest_steps", if_exists=True)

"""create quest tables"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = "20251214_create_quest_tables"
down_revision = "20251213_create_ai_usage"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "quests",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("workspace_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("slug", sa.String(), nullable=False, unique=True),
        sa.Column("title", sa.String(), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column(
            "created_at", sa.DateTime(), server_default=sa.func.now(), nullable=False
        ),
        sa.Column(
            "updated_at", sa.DateTime(), server_default=sa.func.now(), nullable=False
        ),
        sa.ForeignKeyConstraint(
            ["workspace_id"], ["workspaces.id"], ondelete="CASCADE"
        ),
        if_not_exists=True,
    )
    op.create_index(
        "ix_quests_workspace_id",
        "quests",
        ["workspace_id"],
        if_not_exists=True,
    )
    op.create_index(
        "ix_quests_slug",
        "quests",
        ["slug"],
        unique=True,
        if_not_exists=True,
    )

    op.create_table(
        "quest_versions",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("quest_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("number", sa.Integer(), nullable=False, server_default="1"),
        sa.Column("status", sa.String(), nullable=False, server_default="draft"),
        sa.Column(
            "created_at", sa.DateTime(), server_default=sa.func.now(), nullable=False
        ),
        sa.Column("meta", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.ForeignKeyConstraint(["quest_id"], ["quests.id"], ondelete="CASCADE"),
        sa.UniqueConstraint("quest_id", "number", name="uq_quest_version_number"),
        if_not_exists=True,
    )
    op.create_index(
        "ix_quest_versions_quest_id",
        "quest_versions",
        ["quest_id"],
        if_not_exists=True,
    )

    op.create_table(
        "quest_steps",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("version_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("key", sa.String(), nullable=False),
        sa.Column("title", sa.String(), nullable=False),
        sa.Column("type", sa.String(), nullable=False, server_default="normal"),
        sa.Column("content", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column("rewards", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.ForeignKeyConstraint(
            ["version_id"], ["quest_versions.id"], ondelete="CASCADE"
        ),
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
        "quest_transitions",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("version_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("from_step_key", sa.String(), nullable=False),
        sa.Column("to_step_key", sa.String(), nullable=False),
        sa.Column("label", sa.String(), nullable=True),
        sa.Column("condition", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.ForeignKeyConstraint(
            ["version_id"], ["quest_versions.id"], ondelete="CASCADE"
        ),
        if_not_exists=True,
    )
    op.create_index(
        "ix_quest_transitions_version_id",
        "quest_transitions",
        ["version_id"],
        if_not_exists=True,
    )

    op.create_table(
        "quest_step_content_refs",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("step_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("content_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("position", sa.Integer(), nullable=False, server_default="0"),
        sa.ForeignKeyConstraint(["step_id"], ["quest_steps.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["content_id"], ["nodes.id"], ondelete="CASCADE"),
        sa.UniqueConstraint("step_id", "content_id", name="uq_step_content_ref"),
        if_not_exists=True,
    )
    op.create_index(
        "ix_quest_step_content_refs_step_id",
        "quest_step_content_refs",
        ["step_id"],
        if_not_exists=True,
    )
    op.create_index(
        "ix_quest_step_content_refs_content_id",
        "quest_step_content_refs",
        ["content_id"],
        if_not_exists=True,
    )


def downgrade() -> None:
    op.drop_index(
        "ix_quest_step_content_refs_content_id",
        table_name="quest_step_content_refs",
        if_exists=True,
    )
    op.drop_index(
        "ix_quest_step_content_refs_step_id",
        table_name="quest_step_content_refs",
        if_exists=True,
    )
    op.drop_table("quest_step_content_refs", if_exists=True)

    op.drop_index(
        "ix_quest_transitions_version_id",
        table_name="quest_transitions",
        if_exists=True,
    )
    op.drop_table("quest_transitions", if_exists=True)

    op.drop_index(
        "ix_quest_steps_version_id",
        table_name="quest_steps",
        if_exists=True,
    )
    op.drop_table("quest_steps", if_exists=True)

    op.drop_index(
        "ix_quest_versions_quest_id",
        table_name="quest_versions",
        if_exists=True,
    )
    op.drop_table("quest_versions", if_exists=True)

    op.drop_index("ix_quests_slug", table_name="quests", if_exists=True)
    op.drop_index("ix_quests_workspace_id", table_name="quests", if_exists=True)
    op.drop_table("quests", if_exists=True)

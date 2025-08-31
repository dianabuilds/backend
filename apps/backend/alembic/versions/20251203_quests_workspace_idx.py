"""add workspace indexes and columns for quests"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy import inspect
from sqlalchemy.dialects import postgresql


revision = "20251203_quests_workspace_idx"
down_revision = "20251202_worlds_workspace_idx"
branch_labels = None
depends_on = None


def upgrade() -> None:
    bind = op.get_bind()
    inspector = inspect(bind)

    # quests table index
    if "quests" in inspector.get_table_names():
        indexes = {idx["name"] for idx in inspector.get_indexes("quests")}
        if "ix_quests_workspace_id" not in indexes:
            op.create_index("ix_quests_workspace_id", "quests", ["workspace_id"])

    # quest_purchases table
    if "quest_purchases" in inspector.get_table_names():
        cols = {c["name"] for c in inspector.get_columns("quest_purchases")}
        if "workspace_id" not in cols:
            op.add_column(
                "quest_purchases",
                sa.Column("workspace_id", postgresql.UUID(as_uuid=True), nullable=True),
            )
            op.create_foreign_key(
                None, "quest_purchases", "workspaces", ["workspace_id"], ["id"]
            )
            op.execute(
                sa.text(
                    "UPDATE quest_purchases qp SET workspace_id = q.workspace_id FROM quests q WHERE qp.quest_id = q.id"
                )
            )
            op.alter_column("quest_purchases", "workspace_id", nullable=False)
        indexes = {idx["name"] for idx in inspector.get_indexes("quest_purchases")}
        if "ix_quest_purchases_workspace_id" not in indexes:
            op.create_index(
                "ix_quest_purchases_workspace_id", "quest_purchases", ["workspace_id"]
            )

    # quest_progress table
    if "quest_progress" in inspector.get_table_names():
        cols = {c["name"] for c in inspector.get_columns("quest_progress")}
        if "workspace_id" not in cols:
            op.add_column(
                "quest_progress",
                sa.Column("workspace_id", postgresql.UUID(as_uuid=True), nullable=True),
            )
            op.create_foreign_key(
                None, "quest_progress", "workspaces", ["workspace_id"], ["id"]
            )
            op.execute(
                sa.text(
                    "UPDATE quest_progress qp SET workspace_id = q.workspace_id FROM quests q WHERE qp.quest_id = q.id"
                )
            )
            op.alter_column("quest_progress", "workspace_id", nullable=False)
        indexes = {idx["name"] for idx in inspector.get_indexes("quest_progress")}
        if "ix_quest_progress_workspace_id" not in indexes:
            op.create_index(
                "ix_quest_progress_workspace_id", "quest_progress", ["workspace_id"]
            )

    # event_quests table
    if "event_quests" in inspector.get_table_names():
        cols = {c["name"] for c in inspector.get_columns("event_quests")}
        if "workspace_id" not in cols:
            op.add_column(
                "event_quests",
                sa.Column("workspace_id", postgresql.UUID(as_uuid=True), nullable=True),
            )
            op.create_foreign_key(
                None, "event_quests", "workspaces", ["workspace_id"], ["id"]
            )
            op.execute(
                sa.text(
                    "UPDATE event_quests SET workspace_id = (SELECT id FROM workspaces LIMIT 1)"
                )
            )
            op.alter_column("event_quests", "workspace_id", nullable=False)
        indexes = {idx["name"] for idx in inspector.get_indexes("event_quests")}
        if "ix_event_quests_workspace_id" not in indexes:
            op.create_index(
                "ix_event_quests_workspace_id", "event_quests", ["workspace_id"]
            )

    # event_quest_completions table
    if "event_quest_completions" in inspector.get_table_names():
        cols = {c["name"] for c in inspector.get_columns("event_quest_completions")}
        if "workspace_id" not in cols:
            op.add_column(
                "event_quest_completions",
                sa.Column("workspace_id", postgresql.UUID(as_uuid=True), nullable=True),
            )
            op.create_foreign_key(
                None,
                "event_quest_completions",
                "workspaces",
                ["workspace_id"],
                ["id"],
            )
            op.execute(
                sa.text(
                    "UPDATE event_quest_completions eqc SET workspace_id = q.workspace_id FROM event_quests q WHERE eqc.quest_id = q.id"
                )
            )
            op.alter_column("event_quest_completions", "workspace_id", nullable=False)
        indexes = {
            idx["name"] for idx in inspector.get_indexes("event_quest_completions")
        }
        if "ix_event_quest_completions_workspace_id" not in indexes:
            op.create_index(
                "ix_event_quest_completions_workspace_id",
                "event_quest_completions",
                ["workspace_id"],
            )


def downgrade() -> None:
    bind = op.get_bind()
    inspector = inspect(bind)

    if "event_quest_completions" in inspector.get_table_names():
        indexes = {
            idx["name"] for idx in inspector.get_indexes("event_quest_completions")
        }
        if "ix_event_quest_completions_workspace_id" in indexes:
            op.drop_index(
                "ix_event_quest_completions_workspace_id",
                table_name="event_quest_completions",
            )
        cols = {c["name"] for c in inspector.get_columns("event_quest_completions")}
        if "workspace_id" in cols:
            op.drop_column("event_quest_completions", "workspace_id")

    if "event_quests" in inspector.get_table_names():
        indexes = {idx["name"] for idx in inspector.get_indexes("event_quests")}
        if "ix_event_quests_workspace_id" in indexes:
            op.drop_index("ix_event_quests_workspace_id", table_name="event_quests")
        cols = {c["name"] for c in inspector.get_columns("event_quests")}
        if "workspace_id" in cols:
            op.drop_column("event_quests", "workspace_id")

    if "quest_progress" in inspector.get_table_names():
        indexes = {idx["name"] for idx in inspector.get_indexes("quest_progress")}
        if "ix_quest_progress_workspace_id" in indexes:
            op.drop_index("ix_quest_progress_workspace_id", table_name="quest_progress")
        cols = {c["name"] for c in inspector.get_columns("quest_progress")}
        if "workspace_id" in cols:
            op.drop_column("quest_progress", "workspace_id")

    if "quest_purchases" in inspector.get_table_names():
        indexes = {idx["name"] for idx in inspector.get_indexes("quest_purchases")}
        if "ix_quest_purchases_workspace_id" in indexes:
            op.drop_index(
                "ix_quest_purchases_workspace_id", table_name="quest_purchases"
            )
        cols = {c["name"] for c in inspector.get_columns("quest_purchases")}
        if "workspace_id" in cols:
            op.drop_column("quest_purchases", "workspace_id")

    if "quests" in inspector.get_table_names():
        indexes = {idx["name"] for idx in inspector.get_indexes("quests")}
        if "ix_quests_workspace_id" in indexes:
            op.drop_index("ix_quests_workspace_id", table_name="quests")

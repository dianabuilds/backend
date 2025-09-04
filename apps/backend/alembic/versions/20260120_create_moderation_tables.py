from __future__ import annotations

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = "20260120_create_moderation_tables"
down_revision = "20260119_add_workspace_id_to_audit_logs"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "moderation_cases",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("status", sa.String(), nullable=False),
        sa.Column("assignee_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column(
            "created_at", sa.DateTime(), nullable=False, server_default=sa.func.now()
        ),
        if_not_exists=True,
    )
    op.create_index(
        "ix_moderation_cases_status",
        "moderation_cases",
        ["status"],
        if_not_exists=True,
    )
    op.create_index(
        "ix_moderation_cases_assignee_id",
        "moderation_cases",
        ["assignee_id"],
        if_not_exists=True,
    )
    op.create_index(
        "ix_moderation_cases_created_at",
        "moderation_cases",
        ["created_at"],
        if_not_exists=True,
    )

    op.create_table(
        "moderation_labels",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("name", sa.String(), nullable=False),
        sa.Column(
            "created_at", sa.DateTime(), nullable=False, server_default=sa.func.now()
        ),
        if_not_exists=True,
    )
    op.add_column(
        "moderation_labels",
        sa.Column(
            "created_at",
            sa.DateTime(),
            nullable=False,
            server_default=sa.func.now(),
        ),
        if_not_exists=True,
    )
    op.create_index(
        "ix_moderation_labels_created_at",
        "moderation_labels",
        ["created_at"],
        if_not_exists=True,
    )

    op.create_table(
        "case_labels",
        sa.Column("case_id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("label_id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "created_at", sa.DateTime(), nullable=False, server_default=sa.func.now()
        ),
        sa.ForeignKeyConstraint(
            ["case_id"], ["moderation_cases.id"], ondelete="CASCADE"
        ),
        sa.ForeignKeyConstraint(
            ["label_id"], ["moderation_labels.id"], ondelete="CASCADE"
        ),
        if_not_exists=True,
    )
    op.create_index(
        "ix_case_labels_created_at",
        "case_labels",
        ["created_at"],
        if_not_exists=True,
    )

    op.create_table(
        "case_notes",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("case_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("author_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("note", sa.Text(), nullable=False),
        sa.Column(
            "created_at", sa.DateTime(), nullable=False, server_default=sa.func.now()
        ),
        sa.ForeignKeyConstraint(
            ["case_id"], ["moderation_cases.id"], ondelete="CASCADE"
        ),
        if_not_exists=True,
    )
    op.create_index(
        "ix_case_notes_case_id",
        "case_notes",
        ["case_id"],
        if_not_exists=True,
    )
    op.create_index(
        "ix_case_notes_created_at",
        "case_notes",
        ["created_at"],
        if_not_exists=True,
    )

    op.create_table(
        "case_attachments",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("case_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("file_url", sa.String(), nullable=False),
        sa.Column(
            "created_at", sa.DateTime(), nullable=False, server_default=sa.func.now()
        ),
        sa.ForeignKeyConstraint(
            ["case_id"], ["moderation_cases.id"], ondelete="CASCADE"
        ),
        if_not_exists=True,
    )
    op.create_index(
        "ix_case_attachments_case_id",
        "case_attachments",
        ["case_id"],
        if_not_exists=True,
    )
    op.create_index(
        "ix_case_attachments_created_at",
        "case_attachments",
        ["created_at"],
        if_not_exists=True,
    )

    op.create_table(
        "case_events",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("case_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("event_type", sa.String(), nullable=False),
        sa.Column("payload", sa.JSON(), nullable=True),
        sa.Column(
            "created_at", sa.DateTime(), nullable=False, server_default=sa.func.now()
        ),
        sa.ForeignKeyConstraint(
            ["case_id"], ["moderation_cases.id"], ondelete="CASCADE"
        ),
        if_not_exists=True,
    )
    op.create_index(
        "ix_case_events_case_id",
        "case_events",
        ["case_id"],
        if_not_exists=True,
    )
    op.create_index(
        "ix_case_events_created_at",
        "case_events",
        ["created_at"],
        if_not_exists=True,
    )


def downgrade() -> None:
    op.drop_index("ix_case_events_created_at", table_name="case_events", if_exists=True)
    op.drop_index("ix_case_events_case_id", table_name="case_events", if_exists=True)
    op.drop_table("case_events", if_exists=True)

    op.drop_index(
        "ix_case_attachments_created_at", table_name="case_attachments", if_exists=True
    )
    op.drop_index(
        "ix_case_attachments_case_id", table_name="case_attachments", if_exists=True
    )
    op.drop_table("case_attachments", if_exists=True)

    op.drop_index("ix_case_notes_created_at", table_name="case_notes", if_exists=True)
    op.drop_index("ix_case_notes_case_id", table_name="case_notes", if_exists=True)
    op.drop_table("case_notes", if_exists=True)

    op.drop_index("ix_case_labels_created_at", table_name="case_labels", if_exists=True)
    op.drop_table("case_labels", if_exists=True)

    op.drop_index(
        "ix_moderation_labels_created_at",
        table_name="moderation_labels",
        if_exists=True,
    )
    op.drop_table("moderation_labels", if_exists=True)

    op.drop_index(
        "ix_moderation_cases_created_at", table_name="moderation_cases", if_exists=True
    )
    op.drop_index(
        "ix_moderation_cases_assignee_id", table_name="moderation_cases", if_exists=True
    )
    op.drop_index(
        "ix_moderation_cases_status", table_name="moderation_cases", if_exists=True
    )
    op.drop_table("moderation_cases", if_exists=True)

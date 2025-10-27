"""Introduce dedicated notifications schema objects.

Revision ID: 0114_notifications_schema
Revises: 0113_site_global_header_seed
Create Date: 2025-11-02
"""

from __future__ import annotations

import sqlalchemy as sa
from alembic import op
from sqlalchemy import inspect, text
from sqlalchemy.dialects import postgresql

revision = "0114_notifications_schema"
down_revision = "0113_site_global_header_seed"
branch_labels = None
depends_on = None


def _ensure_enum(name: str, values: tuple[str, ...]) -> None:
    quoted = ", ".join(f"'{value}'" for value in values)
    op.execute(
        f"""
        DO $$
        BEGIN
            IF NOT EXISTS (
                SELECT 1 FROM pg_type WHERE typname = '{name}'
            ) THEN
                CREATE TYPE {name} AS ENUM ({quoted});
            END IF;
        END $$;
        """
    )


def _create_index_if_not_exists(sql: str) -> None:
    op.execute(text(sql))


def _fk_exists(inspector, table: str, name: str) -> bool:
    return name in {fk["name"] for fk in inspector.get_foreign_keys(table)}


def upgrade() -> None:
    bind = op.get_bind()
    inspector = inspect(bind)

    _ensure_enum("notificationplacement", ("inbox", "banner"))
    _ensure_enum("notificationtype", ("system", "user"))
    _ensure_enum(
        "notificationbroadcaststatus",
        ("draft", "scheduled", "sending", "sent", "failed", "cancelled"),
    )
    _ensure_enum(
        "notificationaudiencetype",
        ("all_users", "segment", "explicit_users"),
    )
    _ensure_enum(
        "notificationdeliveryrequirement",
        ("mandatory", "default_on", "opt_in", "disabled"),
    )
    _ensure_enum(
        "notificationdigestmode",
        ("instant", "daily", "weekly", "none"),
    )

    if not inspector.has_table("notification_messages"):
        op.create_table(
            "notification_messages",
            sa.Column(
                "id",
                postgresql.UUID(as_uuid=True),
                primary_key=True,
                server_default=sa.text("gen_random_uuid()"),
            ),
            sa.Column(
                "payload_hash", sa.String(length=64), nullable=False, unique=True
            ),
            sa.Column("title", sa.Text(), nullable=False, server_default=sa.text("''")),
            sa.Column(
                "message", sa.Text(), nullable=False, server_default=sa.text("''")
            ),
            sa.Column(
                "type",
                postgresql.ENUM(
                    "system",
                    "user",
                    name="notificationtype",
                    create_type=False,
                ),
                nullable=False,
                server_default=sa.text("'system'"),
            ),
            sa.Column("topic_key", sa.Text(), nullable=True),
            sa.Column("channel_key", sa.Text(), nullable=True),
            sa.Column("cta_label", sa.Text(), nullable=True),
            sa.Column("cta_url", sa.Text(), nullable=True),
            sa.Column(
                "meta",
                postgresql.JSONB(astext_type=sa.Text()),
                nullable=False,
                server_default=sa.text("'{}'::jsonb"),
            ),
            sa.Column(
                "created_at",
                sa.DateTime(timezone=True),
                nullable=False,
                server_default=sa.text("now()"),
            ),
            sa.Column(
                "updated_at",
                sa.DateTime(timezone=True),
                nullable=False,
                server_default=sa.text("now()"),
            ),
        )

    if not inspector.has_table("notification_receipts"):
        op.create_table(
            "notification_receipts",
            sa.Column(
                "id",
                postgresql.UUID(as_uuid=True),
                primary_key=True,
                server_default=sa.text("gen_random_uuid()"),
            ),
            sa.Column("user_id", postgresql.UUID(as_uuid=True), nullable=False),
            sa.Column("message_id", postgresql.UUID(as_uuid=True), nullable=False),
            sa.Column(
                "placement",
                postgresql.ENUM(
                    "inbox",
                    "banner",
                    name="notificationplacement",
                    create_type=False,
                ),
                nullable=False,
                server_default=sa.text("'inbox'"),
            ),
            sa.Column(
                "priority",
                sa.String(length=32),
                nullable=False,
                server_default=sa.text("'normal'"),
            ),
            sa.Column(
                "is_preview",
                sa.Boolean(),
                nullable=False,
                server_default=sa.text("false"),
            ),
            sa.Column(
                "created_at",
                sa.DateTime(timezone=True),
                nullable=False,
                server_default=sa.text("now()"),
            ),
            sa.Column("read_at", sa.DateTime(timezone=True), nullable=True),
            sa.Column("event_id", sa.Text(), nullable=True),
            sa.Column(
                "updated_at",
                sa.DateTime(timezone=True),
                nullable=False,
                server_default=sa.text("now()"),
            ),
        )
    if not _fk_exists(
        inspector, "notification_receipts", "fk_notification_receipts_message_id"
    ):
        op.create_foreign_key(
            "fk_notification_receipts_message_id",
            "notification_receipts",
            "notification_messages",
            ["message_id"],
            ["id"],
            ondelete="CASCADE",
        )
    _create_index_if_not_exists(
        """
        CREATE INDEX IF NOT EXISTS ix_notification_receipts_user_placement_created
        ON notification_receipts (user_id, placement, created_at DESC)
        """
    )
    _create_index_if_not_exists(
        """
        CREATE UNIQUE INDEX IF NOT EXISTS ix_notification_receipts_event_id
        ON notification_receipts (event_id)
        WHERE event_id IS NOT NULL
        """
    )

    if not inspector.has_table("notification_templates"):
        op.create_table(
            "notification_templates",
            sa.Column(
                "id",
                postgresql.UUID(as_uuid=True),
                primary_key=True,
                server_default=sa.text("gen_random_uuid()"),
            ),
            sa.Column("slug", sa.Text(), nullable=False, unique=True),
            sa.Column("name", sa.Text(), nullable=False),
            sa.Column("description", sa.Text(), nullable=True),
            sa.Column("subject", sa.Text(), nullable=True),
            sa.Column("body", sa.Text(), nullable=False),
            sa.Column("locale", sa.Text(), nullable=True),
            sa.Column(
                "variables",
                postgresql.JSONB(astext_type=sa.Text()),
                nullable=True,
            ),
            sa.Column(
                "meta",
                postgresql.JSONB(astext_type=sa.Text()),
                nullable=True,
            ),
            sa.Column("created_by", sa.Text(), nullable=True),
            sa.Column(
                "created_at",
                sa.DateTime(timezone=True),
                nullable=False,
                server_default=sa.text("now()"),
            ),
            sa.Column(
                "updated_at",
                sa.DateTime(timezone=True),
                nullable=False,
                server_default=sa.text("now()"),
            ),
        )

    if not inspector.has_table("notification_broadcasts"):
        op.create_table(
            "notification_broadcasts",
            sa.Column(
                "id",
                postgresql.UUID(as_uuid=True),
                primary_key=True,
                server_default=sa.text("gen_random_uuid()"),
            ),
            sa.Column("title", sa.Text(), nullable=False),
            sa.Column("body", sa.Text(), nullable=True),
            sa.Column("template_id", postgresql.UUID(as_uuid=True), nullable=True),
            sa.Column(
                "audience_type",
                postgresql.ENUM(
                    "all_users",
                    "segment",
                    "explicit_users",
                    name="notificationaudiencetype",
                    create_type=False,
                ),
                nullable=False,
            ),
            sa.Column(
                "audience_filters",
                postgresql.JSONB(astext_type=sa.Text()),
                nullable=True,
            ),
            sa.Column(
                "audience_user_ids",
                postgresql.JSONB(astext_type=sa.Text()),
                nullable=True,
            ),
            sa.Column(
                "status",
                postgresql.ENUM(
                    "draft",
                    "scheduled",
                    "sending",
                    "sent",
                    "failed",
                    "cancelled",
                    name="notificationbroadcaststatus",
                    create_type=False,
                ),
                nullable=False,
                server_default=sa.text("'draft'"),
            ),
            sa.Column("created_by", sa.Text(), nullable=False),
            sa.Column(
                "created_at",
                sa.DateTime(timezone=True),
                nullable=False,
                server_default=sa.text("now()"),
            ),
            sa.Column(
                "updated_at",
                sa.DateTime(timezone=True),
                nullable=False,
                server_default=sa.text("now()"),
            ),
            sa.Column("scheduled_at", sa.DateTime(timezone=True), nullable=True),
            sa.Column("started_at", sa.DateTime(timezone=True), nullable=True),
            sa.Column("finished_at", sa.DateTime(timezone=True), nullable=True),
            sa.Column(
                "total", sa.Integer(), nullable=False, server_default=sa.text("0")
            ),
            sa.Column(
                "sent", sa.Integer(), nullable=False, server_default=sa.text("0")
            ),
            sa.Column(
                "failed", sa.Integer(), nullable=False, server_default=sa.text("0")
            ),
        )
    if not _fk_exists(
        inspector, "notification_broadcasts", "fk_notification_broadcasts_template_id"
    ):
        op.create_foreign_key(
            "fk_notification_broadcasts_template_id",
            "notification_broadcasts",
            "notification_templates",
            ["template_id"],
            ["id"],
            ondelete="SET NULL",
        )
    _create_index_if_not_exists(
        """
        CREATE INDEX IF NOT EXISTS ix_notification_broadcasts_status
        ON notification_broadcasts (status)
        """
    )
    _create_index_if_not_exists(
        """
        CREATE INDEX IF NOT EXISTS ix_notification_broadcasts_scheduled_at
        ON notification_broadcasts (scheduled_at)
        """
    )

    if not inspector.has_table("notification_channels"):
        op.create_table(
            "notification_channels",
            sa.Column("key", sa.Text(), primary_key=True),
            sa.Column("display_name", sa.Text(), nullable=False),
            sa.Column("description", sa.Text(), nullable=True),
            sa.Column("category", sa.Text(), nullable=False),
            sa.Column("feature_flag_slug", sa.Text(), nullable=True),
            sa.Column(
                "flag_fallback_enabled",
                sa.Boolean(),
                nullable=False,
                server_default=sa.text("true"),
            ),
            sa.Column(
                "supports_digest",
                sa.Boolean(),
                nullable=False,
                server_default=sa.text("false"),
            ),
            sa.Column(
                "requires_consent",
                sa.Boolean(),
                nullable=False,
                server_default=sa.text("false"),
            ),
            sa.Column(
                "is_active",
                sa.Boolean(),
                nullable=False,
                server_default=sa.text("true"),
            ),
            sa.Column(
                "position", sa.Integer(), nullable=False, server_default=sa.text("100")
            ),
            sa.Column(
                "meta",
                postgresql.JSONB(astext_type=sa.Text()),
                nullable=False,
                server_default=sa.text("'{}'::jsonb"),
            ),
            sa.Column(
                "created_at",
                sa.DateTime(timezone=True),
                nullable=False,
                server_default=sa.text("now()"),
            ),
            sa.Column(
                "updated_at",
                sa.DateTime(timezone=True),
                nullable=False,
                server_default=sa.text("now()"),
            ),
        )

    if not inspector.has_table("notification_topics"):
        op.create_table(
            "notification_topics",
            sa.Column("key", sa.Text(), primary_key=True),
            sa.Column("category", sa.Text(), nullable=False),
            sa.Column("display_name", sa.Text(), nullable=False),
            sa.Column("description", sa.Text(), nullable=True),
            sa.Column(
                "default_digest",
                postgresql.ENUM(
                    "instant",
                    "daily",
                    "weekly",
                    "none",
                    name="notificationdigestmode",
                    create_type=False,
                ),
                nullable=False,
                server_default=sa.text("'instant'"),
            ),
            sa.Column(
                "default_quiet_hours",
                postgresql.JSONB(astext_type=sa.Text()),
                nullable=False,
                server_default=sa.text("'[]'::jsonb"),
            ),
            sa.Column(
                "position", sa.Integer(), nullable=False, server_default=sa.text("100")
            ),
            sa.Column(
                "meta",
                postgresql.JSONB(astext_type=sa.Text()),
                nullable=False,
                server_default=sa.text("'{}'::jsonb"),
            ),
            sa.Column(
                "created_at",
                sa.DateTime(timezone=True),
                nullable=False,
                server_default=sa.text("now()"),
            ),
            sa.Column(
                "updated_at",
                sa.DateTime(timezone=True),
                nullable=False,
                server_default=sa.text("now()"),
            ),
        )

    if not inspector.has_table("notification_topic_channels"):
        op.create_table(
            "notification_topic_channels",
            sa.Column("topic_key", sa.Text(), nullable=False),
            sa.Column("channel_key", sa.Text(), nullable=False),
            sa.Column(
                "delivery_requirement",
                postgresql.ENUM(
                    "mandatory",
                    "default_on",
                    "opt_in",
                    "disabled",
                    name="notificationdeliveryrequirement",
                    create_type=False,
                ),
                nullable=False,
            ),
            sa.Column("default_opt_in", sa.Boolean(), nullable=True),
            sa.Column(
                "default_digest",
                postgresql.ENUM(
                    "instant",
                    "daily",
                    "weekly",
                    "none",
                    name="notificationdigestmode",
                    create_type=False,
                ),
                nullable=True,
            ),
            sa.Column("feature_flag_slug", sa.Text(), nullable=True),
            sa.Column("flag_fallback_enabled", sa.Boolean(), nullable=True),
            sa.Column(
                "position", sa.Integer(), nullable=False, server_default=sa.text("100")
            ),
            sa.Column(
                "meta",
                postgresql.JSONB(astext_type=sa.Text()),
                nullable=False,
                server_default=sa.text("'{}'::jsonb"),
            ),
            sa.Column(
                "created_at",
                sa.DateTime(timezone=True),
                nullable=False,
                server_default=sa.text("now()"),
            ),
            sa.Column(
                "updated_at",
                sa.DateTime(timezone=True),
                nullable=False,
                server_default=sa.text("now()"),
            ),
            sa.ForeignKeyConstraint(
                ["topic_key"],
                ["notification_topics.key"],
                name="fk_notification_topic_channels_topic",
                ondelete="CASCADE",
            ),
            sa.ForeignKeyConstraint(
                ["channel_key"],
                ["notification_channels.key"],
                name="fk_notification_topic_channels_channel",
                ondelete="CASCADE",
            ),
            sa.PrimaryKeyConstraint("topic_key", "channel_key"),
        )

    if not inspector.has_table("notification_preferences"):
        op.create_table(
            "notification_preferences",
            sa.Column(
                "id",
                sa.BigInteger(),
                primary_key=True,
                autoincrement=True,
            ),
            sa.Column("user_id", postgresql.UUID(as_uuid=True), nullable=False),
            sa.Column("topic_key", sa.Text(), nullable=False),
            sa.Column("channel", sa.Text(), nullable=False),
            sa.Column(
                "opt_in",
                sa.Boolean(),
                nullable=False,
                server_default=sa.text("true"),
            ),
            sa.Column(
                "digest",
                sa.Text(),
                nullable=False,
                server_default=sa.text("'instant'"),
            ),
            sa.Column(
                "quiet_hours",
                postgresql.JSONB(astext_type=sa.Text()),
                nullable=False,
                server_default=sa.text("'[]'::jsonb"),
            ),
            sa.Column(
                "consent_source",
                sa.Text(),
                nullable=False,
                server_default=sa.text("'user'"),
            ),
            sa.Column(
                "consent_version",
                sa.Integer(),
                nullable=False,
                server_default=sa.text("1"),
            ),
            sa.Column("updated_by", sa.Text(), nullable=True),
            sa.Column("request_id", sa.Text(), nullable=True),
            sa.Column(
                "created_at",
                sa.DateTime(timezone=True),
                nullable=False,
                server_default=sa.text("now()"),
            ),
            sa.Column(
                "updated_at",
                sa.DateTime(timezone=True),
                nullable=False,
                server_default=sa.text("now()"),
            ),
            sa.UniqueConstraint(
                "user_id",
                "topic_key",
                "channel",
                name="uq_notification_preferences_user_topic_channel",
            ),
        )
    _create_index_if_not_exists(
        """
        CREATE INDEX IF NOT EXISTS ix_notification_preferences_user
        ON notification_preferences (user_id)
        """
    )
    _create_index_if_not_exists(
        """
        CREATE UNIQUE INDEX IF NOT EXISTS uq_notification_preferences_user_topic_channel_idx
        ON notification_preferences (user_id, topic_key, channel)
        """
    )

    if not inspector.has_table("notification_consent_audit"):
        op.create_table(
            "notification_consent_audit",
            sa.Column(
                "id",
                sa.BigInteger(),
                primary_key=True,
                autoincrement=True,
            ),
            sa.Column("user_id", postgresql.UUID(as_uuid=True), nullable=False),
            sa.Column("topic_key", sa.Text(), nullable=False),
            sa.Column("channel", sa.Text(), nullable=False),
            sa.Column(
                "previous_state",
                postgresql.JSONB(astext_type=sa.Text()),
                nullable=True,
            ),
            sa.Column(
                "new_state",
                postgresql.JSONB(astext_type=sa.Text()),
                nullable=False,
            ),
            sa.Column("source", sa.Text(), nullable=False),
            sa.Column("changed_by", sa.Text(), nullable=True),
            sa.Column("request_id", sa.Text(), nullable=True),
            sa.Column(
                "changed_at",
                sa.DateTime(timezone=True),
                nullable=False,
                server_default=sa.text("now()"),
            ),
        )
    _create_index_if_not_exists(
        """
        CREATE INDEX IF NOT EXISTS ix_notification_consent_audit_user
        ON notification_consent_audit (user_id)
        """
    )


def downgrade() -> None:
    for stmt in (
        "DROP TABLE IF EXISTS notification_consent_audit CASCADE",
        "DROP TABLE IF EXISTS notification_preferences CASCADE",
        "DROP TABLE IF EXISTS notification_topic_channels CASCADE",
        "DROP TABLE IF EXISTS notification_topics CASCADE",
        "DROP TABLE IF EXISTS notification_channels CASCADE",
        "DROP TABLE IF EXISTS notification_broadcasts CASCADE",
        "DROP TABLE IF EXISTS notification_templates CASCADE",
        "DROP TABLE IF EXISTS notification_receipts CASCADE",
        "DROP TABLE IF EXISTS notification_messages CASCADE",
    ):
        op.execute(text(stmt))

    for enum_name in (
        "notificationdeliveryrequirement",
        "notificationaudiencetype",
        "notificationbroadcaststatus",
        "notificationdigestmode",
        "notificationtype",
        "notificationplacement",
    ):
        op.execute(
            f"""
            DO $$
            BEGIN
                IF EXISTS (SELECT 1 FROM pg_type WHERE typname = '{enum_name}') THEN
                    DROP TYPE {enum_name};
                END IF;
            END $$;
            """
        )

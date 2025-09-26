"""split notifications payload into message and receipt tables

Revision ID: 0028
Revises: 0027
Create Date: 2025-10-01 09:00:00
"""

from __future__ import annotations

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql as pg

revision: str = "0028"
down_revision: str | None = "0027"
branch_labels = None
depends_on = None


def upgrade() -> None:
    notification_type = pg.ENUM("system", "user", name="notificationtype", create_type=False)
    placement_enum = pg.ENUM("inbox", "banner", name="notificationplacement", create_type=False)

    op.create_table(
        "notification_messages",
        sa.Column(
            "id",
            pg.UUID(as_uuid=True),
            primary_key=True,
            server_default=sa.text("gen_random_uuid()"),
        ),
        sa.Column("title", sa.Text(), nullable=False),
        sa.Column("message", sa.Text(), nullable=False),
        sa.Column(
            "type",
            notification_type,
            nullable=False,
            server_default=sa.text("'system'::notificationtype"),
        ),
        sa.Column("topic_key", sa.Text(), nullable=True),
        sa.Column("channel_key", sa.Text(), nullable=True),
        sa.Column("cta_label", sa.Text(), nullable=True),
        sa.Column("cta_url", sa.Text(), nullable=True),
        sa.Column(
            "meta",
            pg.JSONB(astext_type=sa.Text()),
            nullable=False,
            server_default=sa.text("'{}'::jsonb"),
        ),
        sa.Column("payload_hash", sa.Text(), nullable=False),
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
    op.create_unique_constraint(
        "ux_notification_messages_hash",
        "notification_messages",
        ["payload_hash"],
    )
    op.create_index(
        "ix_notification_messages_topic",
        "notification_messages",
        ["topic_key"],
        unique=False,
        postgresql_where=sa.text("topic_key IS NOT NULL"),
    )
    op.create_index(
        "ix_notification_messages_channel",
        "notification_messages",
        ["channel_key"],
        unique=False,
        postgresql_where=sa.text("channel_key IS NOT NULL"),
    )

    op.create_table(
        "notification_receipts",
        sa.Column(
            "id",
            pg.UUID(as_uuid=True),
            primary_key=True,
            server_default=sa.text("gen_random_uuid()"),
        ),
        sa.Column("user_id", pg.UUID(as_uuid=True), nullable=False),
        sa.Column(
            "message_id",
            pg.UUID(as_uuid=True),
            sa.ForeignKey("notification_messages.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "placement",
            placement_enum,
            nullable=False,
            server_default=sa.text("'inbox'::notificationplacement"),
        ),
        sa.Column(
            "priority",
            sa.Text(),
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
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("now()"),
        ),
        sa.Column("event_id", sa.Text(), nullable=True),
    )
    op.create_index(
        "ix_notification_receipts_user",
        "notification_receipts",
        ["user_id", "created_at"],
        unique=False,
    )
    op.create_index(
        "ix_notification_receipts_message",
        "notification_receipts",
        ["message_id"],
        unique=False,
    )
    op.create_index(
        "ix_notification_receipts_user_unread",
        "notification_receipts",
        ["user_id"],
        unique=False,
        postgresql_where=sa.text("read_at IS NULL"),
    )
    op.create_index(
        "ux_notification_receipts_event",
        "notification_receipts",
        ["event_id"],
        unique=True,
        postgresql_where=sa.text("event_id IS NOT NULL"),
    )

    conn = op.get_bind()
    conn.execute(
        sa.text(
            """
            WITH source AS (
                SELECT
                    title,
                    message,
                    CASE
                        WHEN type::text IN ('system', 'user') THEN type::text
                        ELSE 'system'
                    END AS type_value,
                    topic_key,
                    channel_key,
                    cta_label,
                    cta_url,
                    COALESCE(meta, '{}'::jsonb) AS meta,
                    COALESCE(created_at, now()) AS created_at,
                    COALESCE(updated_at, created_at) AS updated_at,
                    md5(
                        coalesce(title, '') || '|' ||
                        coalesce(message, '') || '|' ||
                        coalesce(CASE WHEN type::text IN ('system', 'user') THEN type::text ELSE 'system' END, '') || '|' ||
                        coalesce(topic_key, '') || '|' ||
                        coalesce(channel_key, '') || '|' ||
                        coalesce(cta_label, '') || '|' ||
                        coalesce(cta_url, '') || '|' ||
                        coalesce(meta::text, '{}')
                    ) AS payload_hash
                FROM notifications
            )
            INSERT INTO notification_messages (
                title,
                message,
                type,
                topic_key,
                channel_key,
                cta_label,
                cta_url,
                meta,
                payload_hash,
                created_at,
                updated_at
            )
            SELECT
                title,
                message,
                type_value::notificationtype,
                topic_key,
                channel_key,
                cta_label,
                cta_url,
                meta,
                payload_hash,
                MIN(created_at) AS created_at,
                MAX(updated_at) AS updated_at
            FROM source
            GROUP BY
                payload_hash,
                title,
                message,
                type_value,
                topic_key,
                channel_key,
                cta_label,
                cta_url,
                meta
            ON CONFLICT (payload_hash) DO UPDATE SET
                title = EXCLUDED.title,
                message = EXCLUDED.message,
                type = EXCLUDED.type,
                topic_key = EXCLUDED.topic_key,
                channel_key = EXCLUDED.channel_key,
                cta_label = EXCLUDED.cta_label,
                cta_url = EXCLUDED.cta_url,
                meta = EXCLUDED.meta,
                updated_at = EXCLUDED.updated_at
            """
        )
    )
    conn.execute(
        sa.text(
            """
            WITH source AS (
                SELECT
                    id,
                    user_id,
                    CASE
                        WHEN placement::text IN ('inbox', 'banner') THEN placement::text
                        ELSE 'inbox'
                    END AS placement_value,
                    is_preview,
                    created_at,
                    read_at,
                    COALESCE(updated_at, created_at) AS updated_at,
                    event_id,
                    COALESCE(priority, 'normal') AS priority,
                    title,
                    message,
                    CASE
                        WHEN type::text IN ('system', 'user') THEN type::text
                        ELSE 'system'
                    END AS type_value,
                    topic_key,
                    channel_key,
                    cta_label,
                    cta_url,
                    COALESCE(meta, '{}'::jsonb) AS meta,
                    md5(
                        coalesce(title, '') || '|' ||
                        coalesce(message, '') || '|' ||
                        coalesce(CASE WHEN type::text IN ('system', 'user') THEN type::text ELSE 'system' END, '') || '|' ||
                        coalesce(topic_key, '') || '|' ||
                        coalesce(channel_key, '') || '|' ||
                        coalesce(cta_label, '') || '|' ||
                        coalesce(cta_url, '') || '|' ||
                        coalesce(meta::text, '{}')
                    ) AS payload_hash
                FROM notifications
            )
            INSERT INTO notification_receipts (
                id,
                user_id,
                message_id,
                placement,
                priority,
                is_preview,
                created_at,
                read_at,
                updated_at,
                event_id
            )
            SELECT
                s.id,
                s.user_id,
                m.id,
                s.placement_value::notificationplacement,
                s.priority,
                s.is_preview,
                s.created_at,
                s.read_at,
                s.updated_at,
                s.event_id
            FROM source s
            JOIN notification_messages m ON m.payload_hash = s.payload_hash
            """
        )
    )

    op.drop_table("notifications")


def downgrade() -> None:
    notification_type = pg.ENUM("system", "user", name="notificationtype", create_type=False)
    placement_enum = pg.ENUM("inbox", "banner", name="notificationplacement", create_type=False)

    op.create_table(
        "notifications",
        sa.Column(
            "id",
            pg.UUID(as_uuid=True),
            primary_key=True,
            server_default=sa.text("gen_random_uuid()"),
        ),
        sa.Column("user_id", pg.UUID(as_uuid=True), nullable=False),
        sa.Column("title", sa.Text(), nullable=False),
        sa.Column("message", sa.Text(), nullable=False),
        sa.Column(
            "type",
            notification_type,
            nullable=False,
            server_default=sa.text("'system'::notificationtype"),
        ),
        sa.Column(
            "placement",
            placement_enum,
            nullable=False,
            server_default=sa.text("'inbox'::notificationplacement"),
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
        sa.Column("topic_key", sa.Text(), nullable=True),
        sa.Column("channel_key", sa.Text(), nullable=True),
        sa.Column(
            "priority",
            sa.Text(),
            nullable=False,
            server_default=sa.text("'normal'"),
        ),
        sa.Column("cta_label", sa.Text(), nullable=True),
        sa.Column("cta_url", sa.Text(), nullable=True),
        sa.Column(
            "meta",
            pg.JSONB(astext_type=sa.Text()),
            nullable=False,
            server_default=sa.text("'{}'::jsonb"),
        ),
        sa.Column("event_id", sa.Text(), nullable=True),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("now()"),
        ),
        sa.Column("profile_id", pg.UUID(as_uuid=True), nullable=True),
        sa.Column("status", sa.Text(), nullable=True),
        sa.Column(
            "version",
            sa.Integer(),
            nullable=False,
            server_default=sa.text("1"),
        ),
        sa.Column("visibility", sa.Text(), nullable=True),
        sa.Column("created_by_user_id", pg.UUID(as_uuid=True), nullable=True),
        sa.Column("updated_by_user_id", pg.UUID(as_uuid=True), nullable=True),
    )

    conn = op.get_bind()
    conn.execute(
        sa.text(
            """
            INSERT INTO notifications (
                id,
                user_id,
                title,
                message,
                type,
                placement,
                is_preview,
                created_at,
                read_at,
                topic_key,
                channel_key,
                priority,
                cta_label,
                cta_url,
                meta,
                event_id,
                updated_at,
                profile_id,
                status,
                version,
                visibility,
                created_by_user_id,
                updated_by_user_id
            )
            SELECT
                r.id,
                r.user_id,
                m.title,
                m.message,
                m.type,
                r.placement,
                r.is_preview,
                r.created_at,
                r.read_at,
                m.topic_key,
                m.channel_key,
                r.priority,
                m.cta_label,
                m.cta_url,
                m.meta,
                r.event_id,
                r.updated_at,
                NULL::uuid,
                NULL::text,
                1,
                NULL::text,
                NULL::uuid,
                NULL::uuid
            FROM notification_receipts r
            JOIN notification_messages m ON r.message_id = m.id
            """
        )
    )

    op.create_index(
        "ix_notifications_user",
        "notifications",
        ["user_id", "created_at"],
        unique=False,
    )
    op.create_index(
        "ix_notifications_user_unread",
        "notifications",
        ["user_id"],
        unique=False,
        postgresql_where=sa.text("read_at IS NULL"),
    )
    op.create_index(
        "ix_notifications_topic",
        "notifications",
        ["topic_key"],
        unique=False,
        postgresql_where=sa.text("topic_key IS NOT NULL"),
    )
    op.create_index(
        "ix_notifications_channel",
        "notifications",
        ["channel_key"],
        unique=False,
        postgresql_where=sa.text("channel_key IS NOT NULL"),
    )
    op.create_index(
        "ux_notifications_event_id",
        "notifications",
        ["event_id"],
        unique=True,
        postgresql_where=sa.text("event_id IS NOT NULL"),
    )

    op.drop_index("ux_notification_receipts_event", table_name="notification_receipts")
    op.drop_index("ix_notification_receipts_user_unread", table_name="notification_receipts")
    op.drop_index("ix_notification_receipts_message", table_name="notification_receipts")
    op.drop_index("ix_notification_receipts_user", table_name="notification_receipts")
    op.drop_index("ix_notification_messages_channel", table_name="notification_messages")
    op.drop_index("ix_notification_messages_topic", table_name="notification_messages")
    op.drop_constraint(
        "ux_notification_messages_hash",
        "notification_messages",
        type_="unique",
    )

    op.drop_table("notification_receipts")
    op.drop_table("notification_messages")

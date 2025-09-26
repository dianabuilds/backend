"""notification matrix foundations



Revision ID: 0019

Revises: 0018

Create Date: 2025-09-24

"""

from __future__ import annotations

from typing import Any

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql as pg

revision: str = "0019"

down_revision: str | None = "0018"

branch_labels = None

depends_on = None


def upgrade() -> None:

    op.execute(sa.text("DROP TYPE IF EXISTS notification_delivery_requirement CASCADE"))

    op.execute(
        sa.text(
            "CREATE TYPE notification_delivery_requirement AS ENUM ('mandatory', 'default_on', 'opt_in', 'disabled')"
        )
    )

    delivery_enum = pg.ENUM(
        "mandatory",
        "default_on",
        "opt_in",
        "disabled",
        name="notification_delivery_requirement",
        create_type=False,
    )

    op.create_table(
        "notification_channels",
        sa.Column("key", sa.Text(), primary_key=True),
        sa.Column("display_name", sa.Text(), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("category", sa.Text(), nullable=False, server_default=sa.text("'core'")),
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
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.text("true")),
        sa.Column(
            "position",
            sa.Integer(),
            nullable=False,
            server_default=sa.text("100"),
        ),
        sa.Column(
            "meta",
            pg.JSONB,
            nullable=False,
            server_default=sa.text("'{}'::jsonb"),
        ),
        sa.Column(
            "created_at",
            sa.TIMESTAMP(timezone=True),
            nullable=False,
            server_default=sa.text("now()"),
        ),
        sa.Column(
            "updated_at",
            sa.TIMESTAMP(timezone=True),
            nullable=False,
            server_default=sa.text("now()"),
        ),
    )

    op.create_table(
        "notification_topics",
        sa.Column("key", sa.Text(), primary_key=True),
        sa.Column("category", sa.Text(), nullable=False, server_default=sa.text("'system'")),
        sa.Column("display_name", sa.Text(), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column(
            "default_digest",
            sa.Text(),
            nullable=False,
            server_default=sa.text("'instant'"),
        ),
        sa.Column(
            "default_quiet_hours",
            pg.JSONB,
            nullable=False,
            server_default=sa.text("'[]'::jsonb"),
        ),
        sa.Column(
            "position",
            sa.Integer(),
            nullable=False,
            server_default=sa.text("100"),
        ),
        sa.Column(
            "meta",
            pg.JSONB,
            nullable=False,
            server_default=sa.text("'{}'::jsonb"),
        ),
        sa.Column(
            "created_at",
            sa.TIMESTAMP(timezone=True),
            nullable=False,
            server_default=sa.text("now()"),
        ),
        sa.Column(
            "updated_at",
            sa.TIMESTAMP(timezone=True),
            nullable=False,
            server_default=sa.text("now()"),
        ),
    )

    op.create_table(
        "notification_topic_channels",
        sa.Column(
            "topic_key",
            sa.Text(),
            sa.ForeignKey("notification_topics.key", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "channel_key",
            sa.Text(),
            sa.ForeignKey("notification_channels.key", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("delivery_requirement", delivery_enum, nullable=False),
        sa.Column("default_opt_in", sa.Boolean(), nullable=True),
        sa.Column("default_digest", sa.Text(), nullable=True),
        sa.Column("feature_flag_slug", sa.Text(), nullable=True),
        sa.Column("flag_fallback_enabled", sa.Boolean(), nullable=True),
        sa.Column(
            "position",
            sa.Integer(),
            nullable=False,
            server_default=sa.text("100"),
        ),
        sa.Column(
            "meta",
            pg.JSONB,
            nullable=False,
            server_default=sa.text("'{}'::jsonb"),
        ),
        sa.Column(
            "created_at",
            sa.TIMESTAMP(timezone=True),
            nullable=False,
            server_default=sa.text("now()"),
        ),
        sa.Column(
            "updated_at",
            sa.TIMESTAMP(timezone=True),
            nullable=False,
            server_default=sa.text("now()"),
        ),
        sa.PrimaryKeyConstraint("topic_key", "channel_key", name="pk_notification_topic_channels"),
    )

    op.create_index(
        "ix_notification_topic_channels_topic",
        "notification_topic_channels",
        ["topic_key", "delivery_requirement"],
    )

    op.add_column(
        "notification_preferences",
        sa.Column(
            "consent_source",
            sa.Text(),
            nullable=False,
            server_default=sa.text("'user'"),
        ),
    )

    op.add_column(
        "notification_preferences",
        sa.Column(
            "consent_version",
            sa.Integer(),
            nullable=False,
            server_default=sa.text("1"),
        ),
    )

    op.add_column(
        "notification_preferences",
        sa.Column("updated_by", sa.Text(), nullable=True),
    )

    op.add_column(
        "notification_preferences",
        sa.Column("request_id", sa.Text(), nullable=True),
    )

    op.add_column(
        "notification_preferences",
        sa.Column(
            "created_at",
            sa.TIMESTAMP(timezone=True),
            nullable=False,
            server_default=sa.text("now()"),
        ),
    )

    op.create_table(
        "notification_consent_audit",
        sa.Column(
            "id",
            pg.UUID(as_uuid=True),
            primary_key=True,
            server_default=sa.text("gen_random_uuid()"),
        ),
        sa.Column("user_id", pg.UUID(as_uuid=True), nullable=False),
        sa.Column("topic_key", sa.Text(), nullable=False),
        sa.Column("channel", sa.Text(), nullable=False),
        sa.Column("previous_state", pg.JSONB, nullable=True),
        sa.Column("new_state", pg.JSONB, nullable=False),
        sa.Column("source", sa.Text(), nullable=True),
        sa.Column("changed_by", sa.Text(), nullable=True),
        sa.Column("request_id", sa.Text(), nullable=True),
        sa.Column(
            "changed_at",
            sa.TIMESTAMP(timezone=True),
            nullable=False,
            server_default=sa.text("now()"),
        ),
    )

    op.create_index(
        "ix_notification_consent_audit_user",
        "notification_consent_audit",
        ["user_id", "changed_at"],
    )

    op.create_index(
        "ix_notification_consent_audit_topic",
        "notification_consent_audit",
        ["topic_key", "channel"],
    )

    channels_seed = [
        {
            "key": "in_app",
            "display_name": "In-App Inbox",
            "description": "Bell icon inbox and in-product feed.",
            "category": "core",
            "feature_flag_slug": "notifications.channel.in_app",
            "flag_fallback_enabled": True,
            "supports_digest": False,
            "requires_consent": False,
            "is_active": True,
            "position": 10,
            "meta": {
                "badge": True,
                "ux": {"entry": "bell"},
            },
        },
        {
            "key": "email",
            "display_name": "Email",
            "description": "Transactional and digest emails.",
            "category": "core",
            "feature_flag_slug": "notifications.channel.email",
            "flag_fallback_enabled": True,
            "supports_digest": True,
            "requires_consent": False,
            "is_active": True,
            "position": 20,
            "meta": {"digest_options": ["instant", "daily", "weekly"]},
        },
        {
            "key": "push",
            "display_name": "Push",
            "description": "Browser or partner push notifications.",
            "category": "engagement",
            "feature_flag_slug": "notifications.channel.push",
            "flag_fallback_enabled": False,
            "supports_digest": False,
            "requires_consent": True,
            "is_active": True,
            "position": 30,
            "meta": {"frequency_cap": 3},
        },
        {
            "key": "broadcasts",
            "display_name": "Broadcasts",
            "description": "Batch marketing drops surfaced in product.",
            "category": "marketing",
            "feature_flag_slug": "notifications.channel.broadcasts",
            "flag_fallback_enabled": False,
            "supports_digest": False,
            "requires_consent": True,
            "is_active": True,
            "position": 40,
            "meta": {"layout": "separate_tab"},
        },
        {
            "key": "moderator_feed",
            "display_name": "Moderator Feed",
            "description": "Operational signals for moderators and ops teams.",
            "category": "operations",
            "feature_flag_slug": "notifications.channel.moderator",
            "flag_fallback_enabled": True,
            "supports_digest": False,
            "requires_consent": False,
            "is_active": True,
            "position": 50,
            "meta": {"roles": ["moderator", "admin"]},
        },
        {
            "key": "webhook",
            "display_name": "System Webhook",
            "description": "Machine readable events for integrations.",
            "category": "system",
            "feature_flag_slug": "notifications.channel.webhook",
            "flag_fallback_enabled": True,
            "supports_digest": False,
            "requires_consent": False,
            "is_active": True,
            "position": 60,
            "meta": {"payload": "json"},
        },
    ]

    op.bulk_insert(  # type: ignore[arg-type]
        sa.table(
            "notification_channels",
            sa.column("key", sa.Text()),
            sa.column("display_name", sa.Text()),
            sa.column("description", sa.Text()),
            sa.column("category", sa.Text()),
            sa.column("feature_flag_slug", sa.Text()),
            sa.column("flag_fallback_enabled", sa.Boolean()),
            sa.column("supports_digest", sa.Boolean()),
            sa.column("requires_consent", sa.Boolean()),
            sa.column("is_active", sa.Boolean()),
            sa.column("position", sa.Integer()),
            sa.column("meta", pg.JSONB),
        ),
        channels_seed,
    )

    topics_seed = [
        {
            "key": "account.security",
            "category": "system",
            "display_name": "Account Security & Access",
            "description": "Logins, MFA, bans and trust events.",
            "default_digest": "instant",
            "default_quiet_hours": [],
            "position": 10,
            "meta": {"locked_channels": ["in_app"]},
        },
        {
            "key": "economy.billing",
            "category": "system",
            "display_name": "Billing & Payments",
            "description": "Renewals, invoices and premium purchases.",
            "default_digest": "instant",
            "default_quiet_hours": [],
            "position": 20,
            "meta": {},
        },
        {
            "key": "support.reply",
            "category": "system",
            "display_name": "Support Replies",
            "description": "Responses from the support/helpdesk team.",
            "default_digest": "instant",
            "default_quiet_hours": [],
            "position": 30,
            "meta": {},
        },
        {
            "key": "content.new_comment",
            "category": "communication",
            "display_name": "Content Interactions",
            "description": "Comments and reactions on your content.",
            "default_digest": "instant",
            "default_quiet_hours": [],
            "position": 40,
            "meta": {},
        },
        {
            "key": "social.follow",
            "category": "communication",
            "display_name": "New Followers",
            "description": "Users following your profile or spaces.",
            "default_digest": "instant",
            "default_quiet_hours": [],
            "position": 50,
            "meta": {},
        },
        {
            "key": "community.events",
            "category": "communication",
            "display_name": "Community Events",
            "description": "Launches of quests, drops and communities.",
            "default_digest": "instant",
            "default_quiet_hours": [],
            "position": 60,
            "meta": {},
        },
        {
            "key": "community.digest",
            "category": "communication",
            "display_name": "Community Digest",
            "description": "Periodic digest of highlights.",
            "default_digest": "weekly",
            "default_quiet_hours": [],
            "position": 70,
            "meta": {},
        },
        {
            "key": "marketing.campaign",
            "category": "marketing",
            "display_name": "Marketing Broadcasts",
            "description": "Promotional drops and announcements.",
            "default_digest": "instant",
            "default_quiet_hours": [],
            "position": 80,
            "meta": {},
        },
        {
            "key": "marketing.premium_offer",
            "category": "marketing",
            "display_name": "Premium Offers",
            "description": "Premium upsell and retention offers.",
            "default_digest": "instant",
            "default_quiet_hours": [],
            "position": 90,
            "meta": {},
        },
        {
            "key": "system.incident",
            "category": "system",
            "display_name": "System Incidents",
            "description": "Outages and reliability updates.",
            "default_digest": "instant",
            "default_quiet_hours": [],
            "position": 100,
            "meta": {},
        },
        {
            "key": "moderation.queue_update",
            "category": "operations",
            "display_name": "Moderation Queue",
            "description": "Updates to assigned moderation items.",
            "default_digest": "instant",
            "default_quiet_hours": [],
            "position": 110,
            "meta": {"roles": ["moderator"]},
        },
        {
            "key": "reports.escalated",
            "category": "operations",
            "display_name": "Escalated Reports",
            "description": "High severity community escalations.",
            "default_digest": "instant",
            "default_quiet_hours": [],
            "position": 120,
            "meta": {"roles": ["moderator", "admin"]},
        },
    ]

    op.bulk_insert(  # type: ignore[arg-type]
        sa.table(
            "notification_topics",
            sa.column("key", sa.Text()),
            sa.column("category", sa.Text()),
            sa.column("display_name", sa.Text()),
            sa.column("description", sa.Text()),
            sa.column("default_digest", sa.Text()),
            sa.column("default_quiet_hours", pg.JSONB),
            sa.column("position", sa.Integer()),
            sa.column("meta", pg.JSONB),
        ),
        topics_seed,
    )

    def tc(
        topic: str,
        channel: str,
        delivery: str,
        *,
        default_opt_in: bool | None = None,
        default_digest: str | None = None,
        feature_flag: str | None = None,
        fallback: bool | None = None,
        position: int = 100,
    ) -> dict[str, Any]:

        payload: dict[str, Any] = {
            "topic_key": topic,
            "channel_key": channel,
            "delivery_requirement": delivery,
            "position": position,
            "meta": {},
        }

        if default_opt_in is not None:

            payload["default_opt_in"] = default_opt_in

        if default_digest is not None:

            payload["default_digest"] = default_digest

        if feature_flag is not None:

            payload["feature_flag_slug"] = feature_flag

        if fallback is not None:

            payload["flag_fallback_enabled"] = fallback

        return payload

    topic_channels_seed = [
        tc("account.security", "in_app", "mandatory", position=10),
        tc("account.security", "email", "mandatory", position=20),
        tc("account.security", "push", "opt_in", position=30, fallback=False),
        tc("account.security", "webhook", "mandatory", position=40),
        tc("economy.billing", "in_app", "mandatory", position=10),
        tc("economy.billing", "email", "default_on", position=20),
        tc("economy.billing", "push", "opt_in", position=30, fallback=False),
        tc("economy.billing", "webhook", "mandatory", position=40),
        tc("support.reply", "in_app", "default_on", position=10),
        tc("support.reply", "email", "default_on", position=20),
        tc("support.reply", "push", "opt_in", position=30, fallback=False),
        tc("content.new_comment", "in_app", "default_on", position=10),
        tc("content.new_comment", "email", "opt_in", position=20),
        tc("content.new_comment", "push", "default_on", position=30, fallback=False),
        tc("social.follow", "in_app", "default_on", position=10),
        tc("social.follow", "push", "default_on", position=20, fallback=False),
        tc("community.events", "in_app", "default_on", position=10),
        tc("community.events", "email", "opt_in", position=20),
        tc("community.events", "push", "opt_in", position=30, fallback=False),
        tc("community.digest", "in_app", "opt_in", position=10, default_digest="weekly"),
        tc(
            "community.digest",
            "email",
            "default_on",
            position=20,
            default_digest="weekly",
        ),
        tc(
            "marketing.campaign",
            "broadcasts",
            "default_on",
            position=10,
            fallback=False,
        ),
        tc("marketing.campaign", "email", "opt_in", position=20, fallback=False),
        tc(
            "marketing.premium_offer",
            "broadcasts",
            "default_on",
            position=10,
            fallback=False,
        ),
        tc("marketing.premium_offer", "email", "opt_in", position=20, fallback=False),
        tc("system.incident", "in_app", "mandatory", position=10),
        tc("system.incident", "email", "mandatory", position=20),
        tc("system.incident", "push", "default_on", position=30),
        tc("system.incident", "webhook", "mandatory", position=40),
        tc(
            "moderation.queue_update",
            "moderator_feed",
            "mandatory",
            position=10,
            fallback=True,
        ),
        tc("moderation.queue_update", "email", "opt_in", position=20),
        tc(
            "reports.escalated",
            "moderator_feed",
            "mandatory",
            position=10,
            fallback=True,
        ),
        tc("reports.escalated", "email", "default_on", position=20),
    ]

    op.bulk_insert(  # type: ignore[arg-type]
        sa.table(
            "notification_topic_channels",
            sa.column("topic_key", sa.Text()),
            sa.column("channel_key", sa.Text()),
            sa.column("delivery_requirement", delivery_enum),
            sa.column("default_opt_in", sa.Boolean()),
            sa.column("default_digest", sa.Text()),
            sa.column("feature_flag_slug", sa.Text()),
            sa.column("flag_fallback_enabled", sa.Boolean()),
            sa.column("position", sa.Integer()),
            sa.column("meta", pg.JSONB),
        ),
        topic_channels_seed,
    )

    channel_flags = [
        "notifications.channel.in_app",
        "notifications.channel.email",
        "notifications.channel.push",
        "notifications.channel.broadcasts",
        "notifications.channel.moderator",
        "notifications.channel.webhook",
    ]

    insert_flag_stmt = sa.text(
        """
            INSERT INTO feature_flags (key, enabled, payload)
            VALUES (:slug, true, CAST(:payload AS jsonb))
            ON CONFLICT (key) DO NOTHING
            """
    ).bindparams(
        sa.bindparam("slug", type_=sa.Text()),
        sa.bindparam("payload", type_=pg.JSONB),
    )

    bootstrap_payload = {"bootstrap": "notifications"}

    conn = op.get_bind()

    for slug in channel_flags:
        conn.execute(insert_flag_stmt, {"slug": slug, "payload": bootstrap_payload})

    op.execute(
        sa.text(
            "UPDATE notification_preferences SET consent_source = 'user', consent_version = 1, created_at = updated_at WHERE consent_source IS NULL"
        )
    )


def downgrade() -> None:
    conn = op.get_bind()
    conn.execute(
        sa.text(
            "DELETE FROM feature_flags WHERE key IN (:in_app, :email, :push, :broadcasts, :moderator, :webhook)"
        ),
        {
            "in_app": "notifications.channel.in_app",
            "email": "notifications.channel.email",
            "push": "notifications.channel.push",
            "broadcasts": "notifications.channel.broadcasts",
            "moderator": "notifications.channel.moderator",
            "webhook": "notifications.channel.webhook",
        },
    )

    op.drop_index(
        "ix_notification_consent_audit_user",
        table_name="notification_consent_audit",
    )

    op.drop_index(
        "ix_notification_consent_audit_topic",
        table_name="notification_consent_audit",
    )

    op.drop_table("notification_consent_audit")

    op.drop_column("notification_preferences", "created_at")

    op.drop_column("notification_preferences", "request_id")

    op.drop_column("notification_preferences", "updated_by")

    op.drop_column("notification_preferences", "consent_version")

    op.drop_column("notification_preferences", "consent_source")

    op.drop_index(
        "ix_notification_topic_channels_topic",
        table_name="notification_topic_channels",
    )

    op.drop_table("notification_topic_channels")

    op.drop_table("notification_topics")

    op.drop_table("notification_channels")

    op.execute(sa.text("DROP TYPE IF EXISTS notification_delivery_requirement CASCADE"))

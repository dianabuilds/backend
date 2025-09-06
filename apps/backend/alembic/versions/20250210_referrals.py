from __future__ import annotations

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects.postgresql import JSONB, UUID

revision = "20250210_referrals"
down_revision = "20250201_remove_spaces"
branch_labels = None
depends_on = None


def upgrade() -> None:
    bind = op.get_bind()
    inspector = sa.inspect(bind)

    # referral_codes
    if not inspector.has_table("referral_codes"):
        op.create_table(
            "referral_codes",
            sa.Column("id", UUID(as_uuid=True), primary_key=True, nullable=False),
            sa.Column("workspace_id", sa.BigInteger(), sa.ForeignKey("accounts.id"), nullable=False, index=True),
            sa.Column("owner_user_id", UUID(as_uuid=True), sa.ForeignKey("users.id", ondelete="SET NULL"), nullable=True, index=True),
            sa.Column("code", sa.String(), nullable=False),
            sa.Column("uses_count", sa.Integer(), nullable=False, server_default="0"),
            sa.Column("active", sa.Boolean(), nullable=False, server_default=sa.text("true")),
            sa.Column("metadata", JSONB, nullable=False, server_default=sa.text("'{}'")),
            sa.Column("created_by_user_id", UUID(as_uuid=True), sa.ForeignKey("users.id", ondelete="SET NULL"), nullable=True),
            sa.Column("updated_by_user_id", UUID(as_uuid=True), sa.ForeignKey("users.id", ondelete="SET NULL"), nullable=True),
            sa.Column("created_at", sa.DateTime(), nullable=False, server_default=sa.func.now()),
            sa.Column("updated_at", sa.DateTime(), nullable=True),
            sa.UniqueConstraint("workspace_id", "code", name="uq_referral_codes_ws_code"),
        )
        op.create_index(
            "ix_referral_codes_workspace_owner",
            "referral_codes",
            ["workspace_id", "owner_user_id"],
        )
        op.create_index(
            "ix_referral_codes_workspace_active",
            "referral_codes",
            ["workspace_id", "active"],
        )

    # referral_events
    if not inspector.has_table("referral_events"):
        op.create_table(
            "referral_events",
            sa.Column("id", UUID(as_uuid=True), primary_key=True, nullable=False),
            sa.Column("workspace_id", sa.BigInteger(), sa.ForeignKey("accounts.id"), nullable=False, index=True),
            sa.Column("code_id", UUID(as_uuid=True), sa.ForeignKey("referral_codes.id", ondelete="SET NULL"), nullable=True, index=True),
            sa.Column("code", sa.String(), nullable=True),
            sa.Column("referrer_user_id", UUID(as_uuid=True), sa.ForeignKey("users.id", ondelete="SET NULL"), nullable=True, index=True),
            sa.Column("referee_user_id", UUID(as_uuid=True), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True),
            sa.Column("event_type", sa.String(), nullable=False),
            sa.Column("occurred_at", sa.DateTime(), nullable=False, server_default=sa.func.now()),
            sa.Column("metadata", JSONB, nullable=False, server_default=sa.text("'{}'")),
            sa.UniqueConstraint(
                "workspace_id", "referee_user_id", "event_type", name="uq_referral_events_ws_referee_event"
            ),
        )
        op.create_index(
            "ix_referral_events_ws_referrer",
            "referral_events",
            ["workspace_id", "referrer_user_id"],
        )
        op.create_index(
            "ix_referral_events_ws_event_time",
            "referral_events",
            ["workspace_id", "event_type", "occurred_at"],
        )


def downgrade() -> None:  # pragma: no cover
    bind = op.get_bind()
    inspector = sa.inspect(bind)

    if inspector.has_table("referral_events"):
        op.drop_index("ix_referral_events_ws_event_time", table_name="referral_events")
        op.drop_index("ix_referral_events_ws_referrer", table_name="referral_events")
        op.drop_constraint("uq_referral_events_ws_referee_event", "referral_events", type_="unique")
        op.drop_table("referral_events")

    if inspector.has_table("referral_codes"):
        op.drop_index("ix_referral_codes_workspace_active", table_name="referral_codes")
        op.drop_index("ix_referral_codes_workspace_owner", table_name="referral_codes")
        op.drop_constraint("uq_referral_codes_ws_code", "referral_codes", type_="unique")
        op.drop_table("referral_codes")

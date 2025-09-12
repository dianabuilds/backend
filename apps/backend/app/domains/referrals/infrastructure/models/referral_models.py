from __future__ import annotations

from datetime import datetime
from uuid import uuid4

import sqlalchemy as sa

from app.kernel.db import JSONB, UUID, Base


class ReferralCode(Base):
    __tablename__ = "referral_codes"

    id = sa.Column(UUID(), primary_key=True, default=uuid4)

    owner_user_id = sa.Column(
        UUID(), sa.ForeignKey("users.id", ondelete="SET NULL"), nullable=True, index=True
    )
    code = sa.Column(sa.String, nullable=False)
    uses_count = sa.Column(sa.Integer, nullable=False, server_default="0")
    active = sa.Column(sa.Boolean, nullable=False, server_default=sa.true())
    # 'metadata' is reserved in SQLAlchemy Declarative; map column with different attribute name
    meta = sa.Column("metadata", JSONB, nullable=False, server_default=sa.text("'{}'"))
    created_by_user_id = sa.Column(
        UUID(), sa.ForeignKey("users.id", ondelete="SET NULL"), nullable=True
    )
    updated_by_user_id = sa.Column(
        UUID(), sa.ForeignKey("users.id", ondelete="SET NULL"), nullable=True
    )
    created_at = sa.Column(sa.DateTime, nullable=False, default=datetime.utcnow)
    updated_at = sa.Column(sa.DateTime, nullable=True, onupdate=datetime.utcnow)


class ReferralEvent(Base):
    __tablename__ = "referral_events"

    id = sa.Column(UUID(), primary_key=True, default=uuid4)

    code_id = sa.Column(
        UUID(), sa.ForeignKey("referral_codes.id", ondelete="SET NULL"), nullable=True, index=True
    )
    code = sa.Column(sa.String, nullable=True)
    referrer_user_id = sa.Column(
        UUID(), sa.ForeignKey("users.id", ondelete="SET NULL"), nullable=True, index=True
    )
    referee_user_id = sa.Column(
        UUID(), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )
    event_type = sa.Column(sa.String, nullable=False)
    occurred_at = sa.Column(sa.DateTime, nullable=False, default=datetime.utcnow, index=True)
    # Map DB column 'metadata' to attribute 'meta' to avoid reserved name clash
    meta = sa.Column("metadata", JSONB, nullable=False, server_default=sa.text("'{}'"))


__all__ = ["ReferralCode", "ReferralEvent"]


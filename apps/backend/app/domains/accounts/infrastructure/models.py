from __future__ import annotations

from datetime import datetime

import sqlalchemy as sa
from sqlalchemy.orm import relationship

from app.providers.db.adapters import JSONB, UUID
from app.providers.db.base import Base
from app.schemas.accounts import AccountKind, AccountRole


class Account(Base):
    __tablename__ = "accounts"

    id = sa.Column(sa.BigInteger, primary_key=True, autoincrement=True)
    name = sa.Column(sa.String, nullable=False)
    slug = sa.Column(sa.String, nullable=False, unique=True, index=True)
    owner_user_id = sa.Column(UUID(), sa.ForeignKey("users.id"), nullable=False, index=True)
    settings_json = sa.Column(JSONB, nullable=False, server_default=sa.text("'{}'"))
    kind = sa.Column(
        sa.Enum(
            AccountKind,
            name="account_kind",
            values_callable=lambda enum: [e.value for e in enum],
        ),
        nullable=False,
        server_default="team",
        default=AccountKind.team,
    )
    is_system = sa.Column(
        sa.Boolean,
        nullable=False,
        server_default=sa.false(),
        default=False,
    )
    created_at = sa.Column(sa.DateTime, default=datetime.utcnow, index=True)
    updated_at = sa.Column(sa.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    members = relationship("AccountMember", back_populates="account", cascade="all, delete-orphan")


class AccountMember(Base):
    __tablename__ = "account_members"
    __table_args__ = (sa.Index("ix_account_members_account_id_role", "account_id", "role"),)

    account_id = sa.Column(sa.BigInteger, sa.ForeignKey("accounts.id"), primary_key=True)
    user_id = sa.Column(UUID(), sa.ForeignKey("users.id"), primary_key=True)
    role = sa.Column(sa.Enum(AccountRole, name="account_role"), nullable=False)
    permissions_json = sa.Column(JSONB, nullable=False, server_default=sa.text("'{}'"))

    account = relationship("Account", back_populates="members")

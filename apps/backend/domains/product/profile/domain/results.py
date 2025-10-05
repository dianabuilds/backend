from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime


@dataclass(frozen=True)
class WalletView:
    address: str | None
    chain_id: str | None
    verified_at: datetime | None


@dataclass(frozen=True)
class ProfileLimitsView:
    can_change_username: bool
    next_username_change_at: datetime | None
    can_change_email: bool
    next_email_change_at: datetime | None


@dataclass(frozen=True)
class ProfileView:
    id: str
    username: str | None
    email: str | None
    pending_email: str | None
    bio: str | None
    avatar_url: str | None
    role: str | None
    wallet: WalletView
    limits: ProfileLimitsView


@dataclass(frozen=True)
class EmailChangeRequest:
    status: str
    pending_email: str
    token: str


__all__ = [
    "EmailChangeRequest",
    "ProfileLimitsView",
    "ProfileView",
    "WalletView",
]

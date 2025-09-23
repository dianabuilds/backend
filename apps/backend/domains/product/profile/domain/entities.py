from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime

from .policies import validate_username


@dataclass
class Profile:
    id: str
    username: str | None = None
    email: str | None = None
    bio: str | None = None
    avatar_url: str | None = None
    role: str | None = None
    wallet_address: str | None = None
    wallet_chain_id: str | None = None
    wallet_verified_at: datetime | None = None
    pending_email: str | None = None
    email_change_requested_at: datetime | None = None
    last_username_change_at: datetime | None = None
    last_email_change_at: datetime | None = None

    def rename(self, username: str) -> None:
        validate_username(username)
        self.username = username

    def with_bio(self, bio: str | None) -> None:
        self.bio = bio

    def with_avatar(self, avatar_url: str | None) -> None:
        self.avatar_url = avatar_url

    def with_email(self, email: str | None) -> None:
        self.email = email

    def with_pending_email(self, email: str | None, requested_at: datetime | None) -> None:
        self.pending_email = email
        self.email_change_requested_at = requested_at

    def with_wallet(
        self,
        *,
        address: str | None,
        chain_id: str | None,
        verified_at: datetime | None,
    ) -> None:
        self.wallet_address = address
        self.wallet_chain_id = chain_id
        self.wallet_verified_at = verified_at

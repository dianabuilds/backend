from __future__ import annotations

from datetime import datetime
from typing import Protocol, runtime_checkable

from domains.product.profile.domain.entities import Profile


@runtime_checkable
class Repo(Protocol):
    async def get(self, user_id: str) -> Profile | None: ...
    async def update_profile(
        self,
        user_id: str,
        *,
        updates: dict[str, object | None],
        set_username_timestamp: bool,
        now: datetime,
    ) -> Profile: ...
    async def email_in_use(self, email: str, exclude_user_id: str | None = None) -> bool: ...
    async def create_email_change_request(
        self,
        user_id: str,
        *,
        email: str,
        token: str,
        requested_at: datetime,
    ) -> None: ...
    async def confirm_email_change(
        self,
        user_id: str,
        *,
        token: str,
        now: datetime,
    ) -> Profile: ...
    async def set_wallet(
        self,
        user_id: str,
        *,
        address: str,
        chain_id: str | None,
        signature: str | None,
        verified_at: datetime,
    ) -> Profile: ...
    async def clear_wallet(self, user_id: str) -> Profile: ...


@runtime_checkable
class Outbox(Protocol):
    def publish(self, topic: str, payload: dict, key: str | None = None) -> None: ...


@runtime_checkable
class IamClient(Protocol):
    def allow(self, subject: dict, action: str, resource: dict) -> bool: ...


__all__ = ["Repo", "Outbox", "IamClient"]

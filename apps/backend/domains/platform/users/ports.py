from __future__ import annotations

from typing import Protocol

from domains.platform.users.domain.models import User


class UsersRepo(Protocol):
    async def get_by_id(self, user_id: str) -> User | None: ...
    async def get_by_email(self, email: str) -> User | None: ...
    async def get_by_wallet(self, wallet_address: str) -> User | None: ...


__all__ = ["UsersRepo"]

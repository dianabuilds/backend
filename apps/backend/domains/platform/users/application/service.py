from __future__ import annotations

from dataclasses import dataclass

from domains.platform.users.domain.models import User
from domains.platform.users.ports import UsersRepo

ROLE_ORDER = {"user": 0, "support": 1, "moderator": 2, "admin": 3}


@dataclass
class UsersService:
    repo: UsersRepo

    async def get(self, user_id: str) -> User | None:
        return await self.repo.get_by_id(user_id)

    async def require_role(self, user_id: str, min_role: str) -> User:
        user = await self.get(user_id)
        if not user or not user.is_active:
            raise PermissionError("user_not_active")
        if ROLE_ORDER.get(user.role, 0) < ROLE_ORDER.get(min_role, 0):
            raise PermissionError("insufficient_role")
        return user


__all__ = ["UsersService", "ROLE_ORDER"]

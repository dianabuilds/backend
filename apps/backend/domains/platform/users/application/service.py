from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime

from domains.platform.users.domain.models import User
from domains.platform.users.ports import UsersRepo
from packages.core.config import Settings

ROLE_ORDER = {"user": 0, "support": 1, "editor": 2, "moderator": 3, "admin": 4}


@dataclass
class UsersService:
    repo: UsersRepo
    settings: Settings

    def _bootstrap_user(self) -> User | None:
        login = (self.settings.auth_bootstrap_login or "").strip()
        password = self.settings.auth_bootstrap_password
        if not login or password is None:
            return None
        role = (self.settings.auth_bootstrap_role or "admin").strip() or "admin"
        return User(
            id=str(self.settings.auth_bootstrap_user_id or "bootstrap-root"),
            email=None,
            wallet_address=None,
            is_active=True,
            role=role,
            username=login,
            created_at=datetime.utcnow(),
        )

    async def get(self, user_id: str) -> User | None:
        identifier = str(user_id or "").strip()
        bootstrap = self._bootstrap_user()
        if bootstrap:
            if (
                identifier == bootstrap.id
                or identifier.lower() == (bootstrap.username or "").lower()
            ):
                return bootstrap
        return await self.repo.get_by_id(user_id)

    async def require_role(self, user_id: str, min_role: str) -> User:
        user = await self.get(user_id)
        if not user or not user.is_active:
            raise PermissionError("user_not_active")
        if ROLE_ORDER.get(user.role, 0) < ROLE_ORDER.get(min_role, 0):
            raise PermissionError("insufficient_role")
        return user


__all__ = ["UsersService", "ROLE_ORDER"]

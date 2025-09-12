from __future__ import annotations

from typing import Protocol

from app.domains.users.infrastructure.models.user import User


class IUserRepository(Protocol):
    async def get_by_email(self, email: str) -> User | None:  # pragma: no cover - контракт
        ...

    async def get_by_username(self, username: str) -> User | None:  # pragma: no cover
        ...

    async def get_by_id(self, user_id) -> User | None:  # pragma: no cover
        ...

    async def create(
        self, *, email: str, password_hash: str, is_active: bool = False
    ) -> User:  # pragma: no cover
        ...

    async def set_password(self, user: User, password_hash: str) -> None:  # pragma: no cover
        ...

    async def set_active(self, user: User, active: bool) -> None:  # pragma: no cover
        ...

    async def update_last_login(self, user: User, when) -> None:  # pragma: no cover
        ...

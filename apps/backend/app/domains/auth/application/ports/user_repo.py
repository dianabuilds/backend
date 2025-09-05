from __future__ import annotations

from typing import Protocol

from app.domains.users.infrastructure.models.user import User


class IUserRepository(Protocol):
    async def get_by_email(self, email: str) -> User | None:  # pragma: no cover - контракт
        ...

    async def create(
        self, *, email: str, password_hash: str, is_active: bool = False
    ) -> User:  # pragma: no cover
        ...

    async def set_password(self, user: User, password_hash: str) -> None:  # pragma: no cover
        ...

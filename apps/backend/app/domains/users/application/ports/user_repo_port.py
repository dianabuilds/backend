from __future__ import annotations

from typing import Any, Protocol

from app.domains.users.infrastructure.models.user import User


class IUserRepository(Protocol):
    async def update_fields(
        self, user: User, data: dict[str, Any]
    ) -> User:  # pragma: no cover - контракт
        ...

    async def soft_delete(self, user: User) -> None:  # pragma: no cover - контракт
        ...

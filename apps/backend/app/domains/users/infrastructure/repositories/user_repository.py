from __future__ import annotations

from datetime import datetime
from typing import Any

from sqlalchemy.ext.asyncio import AsyncSession

from app.domains.users.application.ports.user_repo_port import IUserRepository
from app.domains.users.infrastructure.models.user import User


class UserRepository(IUserRepository):
    def __init__(self, db: AsyncSession) -> None:
        self._db = db

    async def update_fields(self, user: User, data: dict[str, Any]) -> User:
        for field, value in (data or {}).items():
            setattr(user, field, value)
        await self._db.commit()
        await self._db.refresh(user)
        return user

    async def soft_delete(self, user: User) -> None:
        user.is_active = False
        user.deleted_at = datetime.utcnow()
        user.email = None
        user.password_hash = None
        user.username = None
        user.bio = None
        user.avatar_url = None
        user.is_premium = False
        user.premium_until = None
        await self._db.commit()

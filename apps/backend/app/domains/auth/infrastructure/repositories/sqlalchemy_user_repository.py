from __future__ import annotations

from sqlalchemy import select
from datetime import datetime
from sqlalchemy.ext.asyncio import AsyncSession

from app.domains.auth.application.ports.user_repo import IUserRepository
from app.domains.users.infrastructure.models.user import User


class SqlAlchemyUserRepository(IUserRepository):
    def __init__(self, db: AsyncSession) -> None:
        self._db = db

    async def get_by_email(self, email: str) -> User | None:
        res = await self._db.execute(select(User).where(User.email == email))
        return res.scalars().first()

    async def create(self, *, email: str, password_hash: str, is_active: bool = False) -> User:
        user = User(email=email, password_hash=password_hash, is_active=is_active)
        self._db.add(user)
        await self._db.flush()
        return user

    async def set_password(self, user: User, password_hash: str) -> None:
        user.password_hash = password_hash
        await self._db.flush()

    async def get_by_username(self, username: str) -> User | None:
        res = await self._db.execute(select(User).where(User.username == username))
        return res.scalars().first()

    async def get_by_id(self, user_id) -> User | None:
        return await self._db.get(User, user_id)

    async def set_active(self, user: User, active: bool) -> None:
        user.is_active = active
        await self._db.flush()

    async def update_last_login(self, user: User, when: datetime) -> None:
        user.last_login_at = when
        await self._db.flush()

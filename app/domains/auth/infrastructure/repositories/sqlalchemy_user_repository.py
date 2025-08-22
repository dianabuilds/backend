from __future__ import annotations

from sqlalchemy import select
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

from __future__ import annotations

from typing import Any

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncEngine, create_async_engine

from domains.platform.users.domain.models import User
from domains.platform.users.ports import UsersRepo


def _row_to_user(r: Any) -> User:
    return User(
        id=str(r["id"]),
        email=(str(r["email"]) if r["email"] else None),
        wallet_address=(str(r["wallet_address"]) if r["wallet_address"] else None),
        is_active=bool(r["is_active"]),
        role=str(r["role"]),
        username=(str(r["username"]) if r["username"] else None),
        created_at=r["created_at"],
    )


class SQLUsersRepo(UsersRepo):
    def __init__(self, engine: AsyncEngine | str) -> None:
        self._engine: AsyncEngine = (
            create_async_engine(str(engine)) if isinstance(engine, str) else engine
        )

    async def get_by_id(self, user_id: str) -> User | None:
        sql = text(
            "SELECT id, email, wallet_address, is_active, role, username, created_at FROM users WHERE id = :id"
        )
        async with self._engine.begin() as conn:
            r = (await conn.execute(sql, {"id": user_id})).mappings().first()
            return _row_to_user(r) if r else None

    async def get_by_email(self, email: str) -> User | None:
        sql = text(
            "SELECT id, email, wallet_address, is_active, role, username, created_at FROM users WHERE email = :email"
        )
        async with self._engine.begin() as conn:
            r = (await conn.execute(sql, {"email": email})).mappings().first()
            return _row_to_user(r) if r else None

    async def get_by_wallet(self, wallet_address: str) -> User | None:
        sql = text(
            "SELECT id, email, wallet_address, is_active, role, username, created_at FROM users WHERE wallet_address = :w"
        )
        async with self._engine.begin() as conn:
            r = (await conn.execute(sql, {"w": wallet_address})).mappings().first()
            return _row_to_user(r) if r else None


__all__ = ["SQLUsersRepo"]

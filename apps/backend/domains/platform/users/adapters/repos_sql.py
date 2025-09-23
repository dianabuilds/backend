from __future__ import annotations

import uuid as _uuid
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
        if isinstance(engine, str):
            dsn = str(engine)
            # Normalize DSN for asyncpg: strip query (sslmode etc.), set ssl via connect_args
            try:
                from urllib.parse import parse_qsl, urlparse, urlunparse

                u = urlparse(dsn)
                scheme = u.scheme
                if scheme.startswith("postgresql") and not scheme.startswith("postgresql+asyncpg"):
                    scheme = "postgresql+asyncpg"
                q = dict(parse_qsl(u.query))
                ssl_flag = None
                if "ssl" in q:
                    ssl_flag = str(q.get("ssl")).lower() in {"1", "true", "yes"}
                else:
                    sm = str(q.get("sslmode", "")).lower()
                    if sm in {"require", "verify-full", "verify-ca"}:
                        ssl_flag = True
                    elif sm in {"disable", "allow", "prefer", "0", "false"}:
                        ssl_flag = False
                dsn_no_query = urlunparse((scheme, u.netloc, u.path, u.params, "", u.fragment))
            except Exception:
                ssl_flag = None
                dsn_no_query = dsn
            kwargs = {"connect_args": {}}  # type: ignore[var-annotated]
            if ssl_flag is not None:
                kwargs["connect_args"] = {"ssl": ssl_flag}
            self._engine = create_async_engine(dsn_no_query, **kwargs)
        else:
            self._engine = engine

    async def get_by_id(self, user_id: str) -> User | None:
        # If user_id is not a valid UUID, treat it as email and fallback
        try:
            _uuid.UUID(str(user_id))
        except Exception:
            return await self.get_by_email(str(user_id))
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

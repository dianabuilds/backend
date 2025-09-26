from __future__ import annotations

import uuid as _uuid
from typing import Any

from sqlalchemy import text
from sqlalchemy.exc import ProgrammingError
from sqlalchemy.ext.asyncio import AsyncEngine

from domains.platform.users.domain.models import User
from domains.platform.users.ports import UsersRepo
from packages.core.config import sanitize_async_dsn
from packages.core.db import get_async_engine


def _row_to_user(r: Any) -> User:
    role_value = r.get("role") or "user"
    return User(
        id=str(r["id"]),
        email=(str(r["email"]) if r.get("email") else None),
        wallet_address=(str(r["wallet_address"]) if r.get("wallet_address") else None),
        is_active=bool(r["is_active"]),
        role=str(role_value),
        username=(str(r["username"]) if r.get("username") else None),
        created_at=r["created_at"],
    )


class SQLUsersRepo(UsersRepo):
    def __init__(self, engine: AsyncEngine | str) -> None:
        if isinstance(engine, AsyncEngine):
            self._engine = engine
        else:
            sanitized = sanitize_async_dsn(engine)
            self._engine = get_async_engine("users", url=sanitized)
        self._use_roles_table = True
        self._use_role_column = True

    def _build_query(self, where_clause: str) -> str:
        role_expr: str
        joins: list[str] = []
        if self._use_roles_table:
            role_expr = "COALESCE(r.role::text, 'user') AS role"
            joins.append(
                "LEFT JOIN ("
                " SELECT DISTINCT ON (user_id) user_id, role"
                " FROM user_roles"
                " ORDER BY user_id, granted_at DESC"
                ") AS r ON r.user_id = u.id"
            )
        elif self._use_role_column:
            role_expr = "COALESCE(u.role::text, 'user') AS role"
        else:
            role_expr = "'user'::text AS role"
        select_parts = [
            "u.id AS id",
            "u.email AS email",
            "u.wallet_address AS wallet_address",
            "u.is_active AS is_active",
            role_expr,
            "u.username AS username",
            "u.created_at AS created_at",
        ]
        query = ["SELECT", ", ".join(select_parts), "FROM users u"]
        query.extend(joins)
        query.append(where_clause)
        return " ".join(query)

    async def _fetch_one(self, where_clause: str, params: dict[str, Any]) -> User | None:
        sql_text = text(self._build_query(where_clause))
        async with self._engine.begin() as conn:
            try:
                row = (await conn.execute(sql_text, params)).mappings().first()
            except ProgrammingError as exc:
                detail = "".join(str(x) for x in getattr(exc.orig, "args", [exc])).lower()
                message = str(exc).lower()
                combined = f"{detail} {message}"
                if self._use_roles_table and "user_roles" in combined:
                    self._use_roles_table = False
                    return await self._fetch_one(where_clause, params)
                if self._use_role_column and " column" in combined and "role" in combined:
                    self._use_role_column = False
                    return await self._fetch_one(where_clause, params)
                raise
        if not row:
            return None
        return _row_to_user(row)

    async def get_by_id(self, user_id: str) -> User | None:
        try:
            _uuid.UUID(str(user_id))
        except Exception:
            return await self.get_by_email(str(user_id))
        return await self._fetch_one("WHERE u.id = :id", {"id": user_id})

    async def get_by_email(self, email: str) -> User | None:
        return await self._fetch_one("WHERE lower(u.email) = lower(:email)", {"email": email})

    async def get_by_wallet(self, wallet_address: str) -> User | None:
        return await self._fetch_one(
            "WHERE lower(u.wallet_address) = lower(:wallet)", {"wallet": wallet_address}
        )


__all__ = ["SQLUsersRepo"]

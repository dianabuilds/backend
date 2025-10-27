from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from threading import Lock

from sqlalchemy import text
from sqlalchemy.exc import ProgrammingError
from sqlalchemy.ext.asyncio import AsyncEngine
from sqlalchemy.pool import NullPool

from domains.platform.iam.ports.credentials_port import AuthIdentity, CredentialsPort
from packages.core.db import get_async_engine


@dataclass
class SQLCredentialsAdapter(CredentialsPort):
    """Authenticate users against the SQL `users` table."""

    engine: AsyncEngine | None

    def __init__(self, engine: AsyncEngine | str) -> None:
        self.engine_factory: Callable[[], AsyncEngine] | None
        if isinstance(engine, AsyncEngine):
            self.engine = engine
            self.engine_factory = None
        else:
            dsn = str(engine)
            self.engine = None
            self.engine_factory = lambda: get_async_engine(
                "iam-credentials.repo",
                url=dsn,
                cache=False,
                pool_pre_ping=False,
                poolclass=NullPool,
            )
        self._engine_lock = Lock()
        self._use_fallback = False
        self._primary_query = text(
            """
            SELECT u.id, u.email, u.username, u.role, u.is_active
            FROM users AS u
            WHERE u.deleted_at IS NULL
              AND (lower(u.username) = lower(:login) OR lower(u.email) = lower(:login))
              AND u.password_hash IS NOT NULL
              AND u.password_hash = crypt(:password, u.password_hash)
            LIMIT 1
            """
        )
        self._primary_update = text(
            "UPDATE users SET last_login_at = now() WHERE id = :id"
        )
        self._fallback_query = text(
            """
            SELECT u.id,
                   u.email,
                   u.username,
                   COALESCE(roles.roles[1], 'user') AS role,
                   u.is_active
            FROM users AS u
            LEFT JOIN (
                SELECT user_id, array_agg(role::text ORDER BY role) AS roles
                FROM user_roles
                GROUP BY user_id
            ) AS roles ON roles.user_id = u.id
            WHERE (lower(u.username) = lower(:login) OR lower(u.email) = lower(:login))
              AND u.password_hash IS NOT NULL
              AND u.password_hash = crypt(:password, u.password_hash)
            LIMIT 1
            """
        )

    async def authenticate(self, login: str, password: str) -> AuthIdentity | None:
        identifier = login.strip()
        if not identifier:
            return None
        query = self._fallback_query if self._use_fallback else self._primary_query
        engine = self._get_engine()
        async with engine.begin() as conn:
            try:
                row = (
                    (
                        await conn.execute(
                            query, {"login": identifier, "password": password}
                        )
                    )
                    .mappings()
                    .first()
                )
            except ProgrammingError as exc:
                if not self._use_fallback:
                    detail_src = getattr(exc, "orig", exc)
                    detail = str(detail_src).lower()
                    if "undefined" in detail or "does not exist" in detail:
                        self._use_fallback = True
                        return await self.authenticate(login, password)
                raise
            if not row:
                return None
            if not self._use_fallback:
                await conn.execute(self._primary_update, {"id": row["id"]})
        return AuthIdentity(
            id=str(row["id"]),
            email=(str(row["email"]) if row["email"] else None),
            username=(str(row["username"]) if row["username"] else None),
            role=str(row["role"]),
            is_active=bool(row["is_active"]),
        )

    def _get_engine(self) -> AsyncEngine:
        existing = self.engine
        if existing is not None:
            return existing
        factory = self.engine_factory
        if factory is None:
            raise RuntimeError("credentials engine is not configured")
        with self._engine_lock:
            if self.engine is None:
                self.engine = factory()
            return self.engine


__all__ = ["SQLCredentialsAdapter"]

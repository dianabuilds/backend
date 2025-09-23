from __future__ import annotations

from dataclasses import dataclass

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncEngine, create_async_engine

from domains.platform.iam.ports.credentials_port import AuthIdentity, CredentialsPort


@dataclass
class SQLCredentialsAdapter(CredentialsPort):
    """Authenticate users against the SQL `users` table."""

    engine: AsyncEngine

    def __init__(self, engine: AsyncEngine | str) -> None:
        if isinstance(engine, str):
            self.engine = create_async_engine(engine)
        else:
            self.engine = engine

    async def authenticate(self, login: str, password: str) -> AuthIdentity | None:
        identifier = login.strip()
        if not identifier:
            return None
        query = text(
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
        async with self.engine.begin() as conn:
            row = (
                (await conn.execute(query, {"login": identifier, "password": password}))
                .mappings()
                .first()
            )
            if not row:
                return None
            await conn.execute(
                text("UPDATE users SET last_login_at = now() WHERE id = :id"), {"id": row["id"]}
            )
        return AuthIdentity(
            id=str(row["id"]),
            email=(str(row["email"]) if row["email"] else None),
            username=(str(row["username"]) if row["username"] else None),
            role=str(row["role"]),
            is_active=bool(row["is_active"]),
        )


__all__ = ["SQLCredentialsAdapter"]

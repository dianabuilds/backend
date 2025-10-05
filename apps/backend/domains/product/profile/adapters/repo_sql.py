from __future__ import annotations

import logging
import re
from datetime import datetime
from typing import Any

from sqlalchemy import text
from sqlalchemy.exc import IntegrityError, ProgrammingError
from sqlalchemy.ext.asyncio import AsyncEngine

from domains.product.profile.application.ports import Repo
from domains.product.profile.domain.entities import Profile
from packages.core.db import get_async_engine
from packages.core.sql_fallback import evaluate_sql_backend

from .repo_memory import MemoryRepo, build_default_seed

logger = logging.getLogger(__name__)


class SQLProfileRepo(Repo):
    """Profile repo backed by users table."""

    _COLUMN_EXPRESSIONS: dict[str, tuple[str, str]] = {
        "username": ("u.username", "NULL::text"),
        "email": ("u.email", "NULL::text"),
        "bio": ("u.bio", "NULL::text"),
        "avatar_url": ("u.avatar_url", "NULL::text"),
        "wallet_address": ("u.wallet_address", "NULL::text"),
        "wallet_chain_id": ("u.wallet_chain_id", "NULL::text"),
        "wallet_verified_at": ("u.wallet_verified_at", "NULL::timestamptz"),
    }

    def __init__(self, engine: AsyncEngine | str) -> None:
        if isinstance(engine, AsyncEngine):
            self._engine = engine
        else:
            self._engine = get_async_engine("profile", url=engine)
        self._include_limits = True
        self._include_email_requests = True
        self._include_role_column = True
        self._missing_user_columns: set[str] = set()
        self._memory_overrides: dict[str, dict[str, Any]] = {}
        self._profile_sql = self._build_profile_sql()

    def _build_profile_sql(self) -> str:
        select_parts = ["u.id::text AS id"]
        for col, (expr, fallback) in self._COLUMN_EXPRESSIONS.items():
            if col in self._missing_user_columns:
                if col in {"bio", "avatar_url"}:
                    select_parts.append(f"up.{col} AS {col}")
                else:
                    select_parts.append(f"{fallback} AS {col}")
            else:
                if col in {"bio", "avatar_url"}:
                    select_parts.append(f"COALESCE({expr}, up.{col}) AS {col}")
                else:
                    select_parts.append(f"{expr} AS {col}")
        if self._include_role_column:
            select_parts.append("u.role::text AS role")
        else:
            select_parts.append("'user'::text AS role")
        if self._include_limits:
            select_parts.extend(
                [
                    "lim.last_username_change_at",
                    "lim.last_email_change_at",
                ]
            )
        else:
            select_parts.extend(
                [
                    "NULL::timestamptz AS last_username_change_at",
                    "NULL::timestamptz AS last_email_change_at",
                ]
            )
        if self._include_email_requests:
            select_parts.extend(
                [
                    "req.new_email AS pending_email",
                    "req.requested_at AS email_change_requested_at",
                ]
            )
        else:
            select_parts.extend(
                [
                    "NULL::text AS pending_email",
                    "NULL::timestamptz AS email_change_requested_at",
                ]
            )
        query = ["SELECT", ", ".join(select_parts), "FROM users u"]
        query.append("LEFT JOIN user_profiles up ON up.user_id = u.id")
        if self._include_limits:
            query.append("LEFT JOIN profile_change_limits lim ON lim.user_id = u.id")
        if self._include_email_requests:
            query.append(
                "LEFT JOIN profile_email_change_requests req ON req.user_id = u.id"
            )
        query.append("WHERE u.id = cast(:user_id as uuid)")
        return " ".join(query)

    async def _fetch_profile(self, conn, user_id: str) -> Profile | None:
        attempts = 0
        while True:
            sql = text(self._profile_sql)
            try:
                row = (await conn.execute(sql, {"user_id": user_id})).mappings().first()
                break
            except ProgrammingError as exc:
                detail = "".join(
                    str(x) for x in getattr(exc.orig, "args", [exc])
                ).lower()
                message = str(exc).lower()
                combined = f"{detail} {message}"
                adjusted = False
                if (
                    self._include_email_requests
                    and "profile_email_change_requests" in combined
                ):
                    self._include_email_requests = False
                    adjusted = True
                elif self._include_limits and "profile_change_limits" in combined:
                    self._include_limits = False
                    adjusted = True
                else:
                    match = re.search(r'column\s+(?:u\.)?"?([a-z_]+)"?', combined)
                    if match:
                        missing = match.group(1)
                        if missing in self._COLUMN_EXPRESSIONS:
                            self._missing_user_columns.add(missing)
                            adjusted = True
                        elif missing == "role":
                            self._include_role_column = False
                            adjusted = True
                if not adjusted:
                    raise
                self._profile_sql = self._build_profile_sql()
                if conn.in_transaction():
                    await conn.rollback()
                    await conn.begin()
                attempts += 1
                if attempts > 5:
                    raise
                continue
        if not row:
            return None
        profile = Profile(
            id=str(row["id"]),
            username=row.get("username"),
            email=row.get("email"),
            bio=row.get("bio"),
            avatar_url=row.get("avatar_url"),
            role=row.get("role") or "user",
            wallet_address=row.get("wallet_address"),
            wallet_chain_id=row.get("wallet_chain_id"),
            wallet_verified_at=row.get("wallet_verified_at"),
            pending_email=row.get("pending_email"),
            email_change_requested_at=row.get("email_change_requested_at"),
            last_username_change_at=row.get("last_username_change_at"),
            last_email_change_at=row.get("last_email_change_at"),
        )
        overrides = self._memory_overrides.get(user_id)
        if overrides:
            for key, value in overrides.items():
                setattr(profile, key, value)
        return profile

    async def get(self, user_id: str) -> Profile | None:
        async with self._engine.connect() as conn:
            return await self._fetch_profile(conn, user_id)

    async def update_profile(
        self,
        user_id: str,
        *,
        updates: dict[str, object | None],
        set_username_timestamp: bool,
        now: datetime,
    ) -> Profile:
        async with self._engine.begin() as conn:
            profile = await self._fetch_profile(conn, user_id)
            if not profile:
                raise ValueError("profile_not_found")

            filtered_updates: dict[str, Any] = {}
            profile_table_updates: dict[str, Any] = {}
            for key, value in updates.items():
                if key in {"bio", "avatar_url"}:
                    profile_table_updates[key] = value
                if key in {"username", "bio", "avatar_url"}:
                    if key in self._missing_user_columns and key in {
                        "bio",
                        "avatar_url",
                    }:
                        continue
                    filtered_updates[key] = value

            if filtered_updates:
                assignments = []
                params: dict[str, Any] = {"user_id": user_id}
                if "username" in filtered_updates:
                    assignments.append("username = :username")
                    params["username"] = filtered_updates["username"]
                if "bio" in filtered_updates:
                    assignments.append("bio = :bio")
                    params["bio"] = filtered_updates["bio"]
                if "avatar_url" in filtered_updates:
                    assignments.append("avatar_url = :avatar_url")
                    params["avatar_url"] = filtered_updates["avatar_url"]
                assignments.append("updated_at = now()")
                sql = text(
                    f"""
                    UPDATE users
                    SET {', '.join(assignments)}
                    WHERE id = :user_id
                    """
                )
                try:
                    await conn.execute(sql, params)
                except IntegrityError as exc:
                    raise ValueError("username_taken") from exc

            if profile_table_updates:
                current_bio = getattr(profile, "bio", None)
                current_avatar = getattr(profile, "avatar_url", None)
                bio_value = profile_table_updates.get("bio", current_bio)
                avatar_value = profile_table_updates.get("avatar_url", current_avatar)
                await conn.execute(
                    text(
                        """
                        INSERT INTO user_profiles (user_id, avatar_url, bio, created_at, updated_at)
                        VALUES (cast(:user_id as uuid), :avatar_url, :bio, now(), now())
                        ON CONFLICT (user_id) DO UPDATE SET
                            avatar_url = :avatar_url,
                            bio = :bio,
                            updated_at = now()
                        """
                    ),
                    {"user_id": user_id, "avatar_url": avatar_value, "bio": bio_value},
                )
                overrides = self._memory_overrides.get(user_id)
                if overrides:
                    overrides.pop("bio", None)
                    overrides.pop("avatar_url", None)
                    if not overrides:
                        self._memory_overrides.pop(user_id, None)

            if set_username_timestamp and self._include_limits:
                await conn.execute(
                    text(
                        """
                        INSERT INTO profile_change_limits (user_id, last_username_change_at)
                        VALUES (cast(:user_id as uuid), :ts)
                        ON CONFLICT (user_id) DO UPDATE SET last_username_change_at = EXCLUDED.last_username_change_at
                        """
                    ),
                    {"user_id": user_id, "ts": now},
                )

        profile_after = await self.get(user_id)
        if profile_after is None:
            raise ValueError("profile_not_found")
        return profile_after

    async def email_in_use(
        self, email: str, exclude_user_id: str | None = None
    ) -> bool:
        async with self._engine.connect() as conn:
            params = {"email": email}
            conditions = "lower(email) = lower(:email)"
            if exclude_user_id:
                conditions += " AND id <> cast(:id as uuid)"
                params["id"] = exclude_user_id
            row = (
                await conn.execute(
                    text(f"SELECT 1 FROM users WHERE {conditions} LIMIT 1"),
                    params,
                )
            ).first()
            if row:
                return True
            if not self._include_email_requests:
                return False
            pending_sql = "SELECT 1 FROM profile_email_change_requests WHERE lower(new_email) = lower(:email)"
            pending_params: dict[str, Any] = {"email": email}
            if exclude_user_id:
                pending_sql += " AND user_id <> cast(:id as uuid)"
                pending_params["id"] = exclude_user_id
            pending_sql += " LIMIT 1"
            row = (await conn.execute(text(pending_sql), pending_params)).first()
            return bool(row)

    async def create_email_change_request(
        self,
        user_id: str,
        *,
        email: str,
        token: str,
        requested_at: datetime,
    ) -> None:
        if not self._include_email_requests:
            raise ValueError("email_change_unavailable")
        async with self._engine.begin() as conn:
            sql = text(
                """
                INSERT INTO profile_email_change_requests (user_id, token, new_email, requested_at)
                VALUES (cast(:user_id as uuid), :token, :email, :requested_at)
                ON CONFLICT (user_id) DO UPDATE
                    SET token = EXCLUDED.token,
                        new_email = EXCLUDED.new_email,
                        requested_at = EXCLUDED.requested_at
                """
            )
            await conn.execute(
                sql,
                {
                    "user_id": user_id,
                    "token": token,
                    "email": email,
                    "requested_at": requested_at,
                },
            )
            if self._include_limits:
                await conn.execute(
                    text(
                        """
                        INSERT INTO profile_change_limits (user_id, last_email_change_at)
                        VALUES (cast(:user_id as uuid), NULL)
                        ON CONFLICT (user_id) DO NOTHING
                        """
                    ),
                    {"user_id": user_id},
                )

    async def confirm_email_change(
        self,
        user_id: str,
        *,
        token: str,
        now: datetime,
    ) -> Profile:
        if not self._include_email_requests:
            raise ValueError("email_change_unavailable")
        async with self._engine.begin() as conn:
            row = (
                (
                    await conn.execute(
                        text(
                            """
                        SELECT new_email
                        FROM profile_email_change_requests
                        WHERE user_id = cast(:user_id as uuid) AND token = :token
                        """
                        ),
                        {"user_id": user_id, "token": token},
                    )
                )
                .mappings()
                .first()
            )
            if not row:
                raise ValueError("email_change_not_found")
            new_email = row["new_email"]
            try:
                await conn.execute(
                    text(
                        """
                        UPDATE users
                        SET email = :email,
                            updated_at = now()
                        WHERE id = :id
                        """
                    ),
                    {"id": user_id, "email": new_email},
                )
            except IntegrityError as exc:
                raise ValueError("email_taken") from exc

            if self._include_limits:
                await conn.execute(
                    text(
                        """
                        INSERT INTO profile_change_limits (user_id, last_email_change_at)
                        VALUES (cast(:user_id as uuid), :ts)
                        ON CONFLICT (user_id) DO UPDATE SET last_email_change_at = EXCLUDED.last_email_change_at
                        """
                    ),
                    {"user_id": user_id, "ts": now},
                )

            await conn.execute(
                text(
                    "DELETE FROM profile_email_change_requests WHERE user_id = cast(:user_id as uuid)"
                ),
                {"user_id": user_id},
            )

        profile_after = await self.get(user_id)
        if profile_after is None:
            raise ValueError("profile_not_found")
        return profile_after

    async def set_wallet(
        self,
        user_id: str,
        *,
        address: str,
        chain_id: str | None,
        signature: str | None,
        verified_at: datetime,
    ) -> Profile:
        async with self._engine.begin() as conn:
            sql = text(
                """
                UPDATE users
                SET wallet_address = :address,
                    wallet_chain_id = :chain_id,
                    wallet_signature = :signature,
                    wallet_verified_at = :verified_at,
                    wallet_nonce = NULL
                WHERE id = :id
                """
            )
            try:
                await conn.execute(
                    sql,
                    {
                        "id": user_id,
                        "address": address,
                        "chain_id": chain_id,
                        "signature": signature,
                        "verified_at": verified_at,
                    },
                )
            except IntegrityError as exc:
                raise ValueError("wallet_taken") from exc

        profile_after = await self.get(user_id)
        if profile_after is None:
            raise ValueError("profile_not_found")
        return profile_after

    async def clear_wallet(self, user_id: str) -> Profile:
        async with self._engine.begin() as conn:
            sql = text(
                """
                UPDATE users
                SET wallet_address = NULL,
                    wallet_chain_id = NULL,
                    wallet_signature = NULL,
                    wallet_verified_at = NULL
                WHERE id = :id
                """
            )
            await conn.execute(sql, {"id": user_id})

        profile_after = await self.get(user_id)
        if profile_after is None:
            raise ValueError("profile_not_found")
        return profile_after


def _log_fallback(reason: str | None, error: Exception | None = None) -> None:
    if error is not None:
        logger.warning(
            "profile repo: falling back to in-memory backend due to SQL error: %s",
            error,
        )
        return
    if not reason:
        logger.debug("profile repo: using in-memory backend")
        return
    level = logging.DEBUG
    lowered = reason.lower()
    if "invalid" in lowered or "empty" in lowered:
        level = logging.WARNING
    elif "not configured" in lowered or "helpers unavailable" in lowered:
        level = logging.INFO
    logger.log(level, "profile repo: using in-memory backend (%s)", reason)


def create_repo(settings) -> Repo:
    decision = evaluate_sql_backend(settings)
    if not decision.dsn:
        _log_fallback(decision.reason)
        return MemoryRepo(seed=build_default_seed())
    try:
        return SQLProfileRepo(decision.dsn)
    except Exception as exc:  # pragma: no cover - defensive fallback
        _log_fallback(decision.reason or "engine initialization failed", error=exc)
        return MemoryRepo()


__all__ = [
    "SQLProfileRepo",
    "create_repo",
]

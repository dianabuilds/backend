from __future__ import annotations

import asyncio
from datetime import datetime
from typing import Any

from sqlalchemy import text
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncEngine, create_async_engine

from domains.product.profile.application.ports import Repo
from domains.product.profile.domain.entities import Profile


class SQLProfileRepo(Repo):
    """Profile repo backed by users table."""

    def __init__(self, engine: AsyncEngine | str) -> None:
        self._engine: AsyncEngine = (
            create_async_engine(str(engine)) if isinstance(engine, str) else engine
        )

    async def _fetch_profile(self, conn, user_id: str) -> Profile | None:
        sql = text(
            """
            SELECT
                u.id::text AS id,
                u.username,
                u.email,
                u.bio,
                u.avatar_url,
                u.role::text AS role,
                u.wallet_address,
                u.wallet_chain_id,
                u.wallet_verified_at,
                lim.last_username_change_at,
                lim.last_email_change_at,
                req.new_email AS pending_email,
                req.requested_at AS email_change_requested_at
            FROM users u
            LEFT JOIN profile_change_limits lim ON lim.user_id = u.id
            LEFT JOIN profile_email_change_requests req ON req.user_id = u.id
            WHERE u.id = :id
            """
        )
        row = (await conn.execute(sql, {"id": user_id})).mappings().first()
        if not row:
            return None
        return Profile(
            id=str(row["id"]),
            username=row.get("username"),
            email=row.get("email"),
            bio=row.get("bio"),
            avatar_url=row.get("avatar_url"),
            role=row.get("role"),
            wallet_address=row.get("wallet_address"),
            wallet_chain_id=row.get("wallet_chain_id"),
            wallet_verified_at=row.get("wallet_verified_at"),
            pending_email=row.get("pending_email"),
            email_change_requested_at=row.get("email_change_requested_at"),
            last_username_change_at=row.get("last_username_change_at"),
            last_email_change_at=row.get("last_email_change_at"),
        )

    def _run_async(self, coro):
        try:
            loop = asyncio.get_running_loop()
        except RuntimeError:
            return asyncio.run(coro)
        else:
            return loop.run_until_complete(coro)  # type: ignore[misc]

    def get(self, user_id: str) -> Profile | None:
        async def _run() -> Profile | None:
            async with self._engine.begin() as conn:
                return await self._fetch_profile(conn, user_id)

        return self._run_async(_run())

    def update_profile(
        self,
        user_id: str,
        *,
        updates: dict[str, object | None],
        set_username_timestamp: bool,
        now: datetime,
    ) -> Profile:
        async def _run() -> Profile:
            async with self._engine.begin() as conn:
                profile = await self._fetch_profile(conn, user_id)
                if not profile:
                    raise ValueError("profile_not_found")

                filtered_updates: dict[str, Any] = {}
                for key, value in updates.items():
                    if key in {"username", "bio", "avatar_url"}:
                        filtered_updates[key] = value

                if filtered_updates:
                    assignments = []
                    params: dict[str, Any] = {"id": user_id}
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
                        WHERE id = :id
                        """
                    )
                    try:
                        await conn.execute(sql, params)
                    except IntegrityError as exc:  # username uniqueness
                        raise ValueError("username_taken") from exc

                if set_username_timestamp:
                    await conn.execute(
                        text(
                            """
                            INSERT INTO profile_change_limits (user_id, last_username_change_at)
                            VALUES (cast(:user_id as uuid), :ts)
                            ON CONFLICT (user_id) DO UPDATE SET last_username_change_at = EXCLUDED.last_username_change_at
                            """
                        ),
                        {"id": user_id, "ts": now},
                    )

                updated = await self._fetch_profile(conn, user_id)
                if not updated:
                    raise ValueError("profile_not_found")
                return updated

        return self._run_async(_run())

    def email_in_use(self, email: str, exclude_user_id: str | None = None) -> bool:
        async def _run() -> bool:
            async with self._engine.begin() as conn:
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
                pending_sql = """
                        SELECT 1 FROM profile_email_change_requests
                        WHERE lower(new_email) = lower(:email)
                    """
                pending_params: dict[str, Any] = {"email": email}
                if exclude_user_id:
                    pending_sql += " AND user_id <> cast(:id as uuid)"
                    pending_params["id"] = exclude_user_id
                pending_sql += " LIMIT 1"
                row = (
                    await conn.execute(
                        text(pending_sql),
                        pending_params,
                    )
                ).first()
                return bool(row)

        return self._run_async(_run())

    def create_email_change_request(
        self,
        user_id: str,
        *,
        email: str,
        token: str,
        requested_at: datetime,
    ) -> None:
        async def _run() -> None:
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
                        "id": id,
                        "token": token,
                        "email": email,
                        "requested_at": requested_at,
                    },
                )

        self._run_async(_run())

    def confirm_email_change(
        self,
        user_id: str,
        *,
        token: str,
        now: datetime,
    ) -> Profile:
        async def _run() -> Profile:
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

                await conn.execute(
                    text(
                        """
                        INSERT INTO profile_change_limits (user_id, last_email_change_at)
                        VALUES (cast(:user_id as uuid), :ts)
                        ON CONFLICT (user_id) DO UPDATE SET last_email_change_at = EXCLUDED.last_email_change_at
                        """
                    ),
                    {"id": user_id, "ts": now},
                )

                await conn.execute(
                    text(
                        "DELETE FROM profile_email_change_requests WHERE user_id = cast(:user_id as uuid)"
                    ),
                    {"id": user_id},
                )

                updated = await self._fetch_profile(conn, user_id)
                if not updated:
                    raise ValueError("profile_not_found")
                return updated

        return self._run_async(_run())

    def set_wallet(
        self,
        user_id: str,
        *,
        address: str,
        chain_id: str | None,
        signature: str | None,
        verified_at: datetime,
    ) -> Profile:
        async def _run() -> Profile:
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
                updated = await self._fetch_profile(conn, user_id)
                if not updated:
                    raise ValueError("profile_not_found")
                return updated

        return self._run_async(_run())

    def clear_wallet(self, user_id: str) -> Profile:
        async def _run() -> Profile:
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
                updated = await self._fetch_profile(conn, user_id)
                if not updated:
                    raise ValueError("profile_not_found")
                return updated

        return self._run_async(_run())


__all__ = ["SQLProfileRepo"]

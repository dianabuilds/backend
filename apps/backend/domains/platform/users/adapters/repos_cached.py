from __future__ import annotations

import json
from typing import Any

import redis.asyncio as redis  # type: ignore

from domains.platform.users.domain.models import User
from domains.platform.users.ports import UsersRepo


def _user_to_json(u: User) -> str:
    return json.dumps(
        {
            "id": u.id,
            "email": u.email,
            "wallet_address": u.wallet_address,
            "is_active": u.is_active,
            "role": u.role,
            "username": u.username,
            "created_at": u.created_at.isoformat(),
        }
    )


def _user_from_map(r: dict[str, Any] | None) -> User | None:
    if not r:
        return None
    # created_at back to datetime
    from datetime import datetime

    return User(
        id=str(r.get("id")),
        email=r.get("email"),
        wallet_address=r.get("wallet_address"),
        is_active=bool(r.get("is_active")),
        role=str(r.get("role")),
        username=r.get("username"),
        created_at=datetime.fromisoformat(str(r.get("created_at"))),
    )


class CachedUsersRepo(UsersRepo):
    def __init__(
        self, base: UsersRepo, client: redis.Redis, ttl_seconds: int = 60
    ) -> None:
        self._base = base
        self._r = client
        self._ttl = ttl_seconds

    def _k_id(self, user_id: str) -> str:
        return f"users:id:{user_id}"

    def _k_email(self, email: str) -> str:
        return f"users:email:{email.lower()}"

    def _k_wallet(self, wallet: str) -> str:
        return f"users:wallet:{wallet.lower()}"

    async def _cache_user(self, u: User) -> None:
        await self._r.set(self._k_id(u.id), _user_to_json(u), ex=self._ttl)
        if u.email:
            await self._r.set(self._k_email(u.email), u.id, ex=self._ttl)
        if u.wallet_address:
            await self._r.set(self._k_wallet(u.wallet_address), u.id, ex=self._ttl)

    async def get_by_id(self, user_id: str) -> User | None:
        raw = await self._r.get(self._k_id(user_id))
        if raw:
            try:
                return _user_from_map(json.loads(raw))
            except Exception:
                pass
        u = await self._base.get_by_id(user_id)
        if u:
            await self._cache_user(u)
        return u

    async def get_by_email(self, email: str) -> User | None:
        user_id = await self._r.get(self._k_email(email))
        if user_id:
            return await self.get_by_id(str(user_id))
        u = await self._base.get_by_email(email)
        if u:
            await self._cache_user(u)
        return u

    async def get_by_wallet(self, wallet_address: str) -> User | None:
        user_id = await self._r.get(self._k_wallet(wallet_address))
        if user_id:
            return await self.get_by_id(str(user_id))
        u = await self._base.get_by_wallet(wallet_address)
        if u:
            await self._cache_user(u)
        return u


__all__ = ["CachedUsersRepo"]

from __future__ import annotations

import secrets

import redis.asyncio as redis  # type: ignore

from apps.backendDDD.domains.platform.iam.ports.verification_port import (
    VerificationTokenStore,
)


class RedisVerificationStore(VerificationTokenStore):
    def __init__(self, client: redis.Redis) -> None:
        self._r = client

    async def create(self, email: str, ttl_seconds: int = 86400) -> str:
        token = secrets.token_urlsafe(24)
        await self._r.set(f"verify:{token}", email, ex=ttl_seconds)
        return token

    async def verify(self, token: str) -> str | None:
        key = f"verify:{token}"
        email = await self._r.get(key)
        if email:
            await self._r.delete(key)
            return str(email)
        return None


__all__ = ["RedisVerificationStore"]

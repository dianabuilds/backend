from __future__ import annotations

import secrets

import redis.asyncio as redis  # type: ignore

from apps.backendDDD.domains.platform.iam.ports.nonce_store_port import NonceStore


class RedisNonceStore(NonceStore):
    def __init__(self, client: redis.Redis) -> None:
        self._r = client

    async def issue(self, user_id: str, ttl_seconds: int = 600) -> str:
        nonce = secrets.token_urlsafe(16)
        await self._r.set(f"siwe:nonce:{user_id}", nonce, ex=ttl_seconds)
        return nonce

    async def verify(self, user_id: str, nonce: str) -> bool:
        key = f"siwe:nonce:{user_id}"
        current = await self._r.get(key)
        if current and str(current) == str(nonce):
            await self._r.delete(key)
            return True
        return False


__all__ = ["RedisNonceStore"]

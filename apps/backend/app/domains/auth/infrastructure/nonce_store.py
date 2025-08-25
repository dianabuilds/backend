from __future__ import annotations

from typing import Optional

try:  # pragma: no cover - optional dependency
    import redis.asyncio as redis
except Exception:  # pragma: no cover
    redis = None  # type: ignore


class NonceStore:
    """Redis-based nonce store with TTL."""

    def __init__(self, client: "redis.Redis", ttl: int) -> None:
        self._client = client
        self._ttl = ttl

    def _key(self, user_id: str) -> str:
        return f"auth:nonce:{user_id}"

    async def set(self, user_id: str, nonce: str) -> None:
        await self._client.set(self._key(user_id), nonce, ex=self._ttl)

    async def pop(self, user_id: str) -> Optional[str]:
        key = self._key(user_id)
        value = await self._client.get(key)
        if value is not None:
            await self._client.delete(key)
        return value


__all__ = ["NonceStore"]

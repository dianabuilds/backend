from __future__ import annotations

try:  # pragma: no cover - optional dependency
    import redis.asyncio as redis
except Exception:  # pragma: no cover
    redis = None  # type: ignore


class VerificationTokenStore:
    """Redis-based verification token store with TTL."""

    def __init__(self, client: redis.Redis, ttl: int) -> None:
        self._client = client
        self._ttl = ttl

    def _key(self, token: str) -> str:
        return f"auth:verify:{token}"

    async def set(self, token: str, user_id: str) -> None:
        await self._client.set(self._key(token), user_id, ex=self._ttl)

    async def pop(self, token: str) -> str | None:
        key = self._key(token)
        value = await self._client.get(key)
        if value is not None:
            await self._client.delete(key)
        return value


__all__ = ["VerificationTokenStore"]

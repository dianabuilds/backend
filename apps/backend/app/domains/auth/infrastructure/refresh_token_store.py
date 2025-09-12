from __future__ import annotations

try:  # pragma: no cover - optional dependency
    import redis.asyncio as redis
except Exception:  # pragma: no cover
    redis = None  # type: ignore


class RedisRefreshTokenStore:
    """Async refresh token store backed by Redis."""

    def __init__(self, client: "redis.Redis", ttl: int | None = None) -> None:
        self._client = client
        self._ttl = ttl

    def _key(self, jti: str) -> str:
        return f"auth:rt:{jti}"

    async def set(self, jti: str, sub: str) -> None:
        if self._ttl:
            await self._client.set(self._key(jti), sub, ex=self._ttl)
        else:
            await self._client.set(self._key(jti), sub)

    async def pop(self, jti: str) -> str | None:
        key = self._key(jti)
        pipe = self._client.pipeline()
        await pipe.get(key)
        await pipe.delete(key)
        res = await pipe.execute()
        val = res[0] if res else None
        return val


__all__ = ["RedisRefreshTokenStore"]

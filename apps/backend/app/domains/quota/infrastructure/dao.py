from __future__ import annotations

from app.providers.cache import Cache
from app.providers.cache import cache as shared_cache


class QuotaCounterDAO:
    """DAO for quota counters stored in cache (Redis)."""

    def __init__(self, cache: Cache | None = None) -> None:
        # use shared cache (Redis if configured)
        self.cache = cache or shared_cache

    @staticmethod
    def _key(key: str, period: str, user_id: str) -> str:
        return f"q:{key}:{period}:{user_id}"

    async def incr(
        self,
        *,
        user_id: str,
        key: str,
        period: str,
        amount: int,
        ttl: int,
    ) -> int:
        redis_key = self._key(key, period, user_id)
        new_value = await self.cache.incr(redis_key, amount)
        if new_value == amount:
            await self.cache.expire(redis_key, ttl)
        return new_value

    async def get(
        self,
        *,
        user_id: str,
        key: str,
        period: str,
    ) -> int:
        redis_key = self._key(key, period, user_id)
        value = await self.cache.get(redis_key)
        return int(value or 0)

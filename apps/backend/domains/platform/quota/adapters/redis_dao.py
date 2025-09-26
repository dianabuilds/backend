from __future__ import annotations

import redis.asyncio as redis  # type: ignore

from domains.platform.quota.ports.dao import QuotaDAO


class RedisQuotaDAO(QuotaDAO):
    def __init__(self, client: redis.Redis) -> None:
        self._r = client

    @staticmethod
    def _key(key: str, period: str, user_id: str) -> str:
        return f"q:{key}:{period}:{user_id}"

    async def incr(self, *, user_id: str, key: str, period: str, amount: int, ttl: int) -> int:
        redis_key = self._key(key, period, user_id)
        new_value = await self._r.incrby(redis_key, amount)
        if int(new_value) == int(amount):
            await self._r.expire(redis_key, ttl)
        return int(new_value)

    async def get(self, *, user_id: str, key: str, period: str) -> int:
        redis_key = self._key(key, period, user_id)
        value = await self._r.get(redis_key)
        return int(value or 0)


__all__ = ["RedisQuotaDAO"]

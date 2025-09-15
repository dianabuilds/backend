from __future__ import annotations

import json
from typing import Any

import redis.asyncio as redis  # type: ignore

from domains.platform.telemetry.ports.rum_port import IRumRepository


class RumRedisRepository(IRumRepository):
    def __init__(
        self, client: redis.Redis, *, key: str = "telemetry:rum", maxlen: int = 1000
    ) -> None:
        self._redis = client
        self._key = key
        self._maxlen = maxlen

    async def add(self, event: dict[str, Any]) -> None:
        data = json.dumps(event, ensure_ascii=False)
        await self._redis.lpush(self._key, data)
        await self._redis.ltrim(self._key, 0, self._maxlen - 1)

    async def list(self, limit: int) -> list[dict[str, Any]]:
        raw = await self._redis.lrange(self._key, 0, limit - 1)
        return [json.loads(item) for item in raw]


__all__ = ["RumRedisRepository"]

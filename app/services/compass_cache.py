from __future__ import annotations

import json
import time
from typing import Any, Dict, Optional

try:
    import redis.asyncio as redis  # type: ignore
except Exception:  # pragma: no cover - optional dependency
    redis = None

from app.core.config import settings


class CompassCache:
    """Cache for compass recommendations."""

    def __init__(self) -> None:
        self.ttl = 15 * 60  # 15 minutes
        self._memory: Dict[str, Dict[str, Any]] = {}
        self._redis: Optional[redis.Redis] = None
        if settings.redis_url and redis is not None:  # pragma: no cover - optional dependency
            try:
                self._redis = redis.from_url(settings.redis_url, decode_responses=True)
            except Exception:  # pragma: no cover
                self._redis = None

    def _key(self, user_id: str | None, node_id: str) -> str:
        uid = user_id or "anon"
        return f"compass:{uid}:{node_id}"

    async def get(self, user_id: str | None, node_id: str) -> Optional[list[str]]:
        key = self._key(user_id, node_id)
        if self._redis is not None:
            data = await self._redis.get(key)
            if data:
                return json.loads(data)
            return None
        value = self._memory.get(key)
        if not value:
            return None
        if value["expires_at"] < time.time():
            self._memory.pop(key, None)
            return None
        return value["data"]

    async def set(self, user_id: str | None, node_id: str, data: list[str]) -> None:
        key = self._key(user_id, node_id)
        if self._redis is not None:
            await self._redis.set(key, json.dumps(data), ex=self.ttl)
            return
        self._memory[key] = {"data": data, "expires_at": time.time() + self.ttl}

    async def invalidate(self, user_id: str | None, node_id: str) -> None:
        key = self._key(user_id, node_id)
        if self._redis is not None:
            await self._redis.delete(key)
            return
        self._memory.pop(key, None)

    async def invalidate_all_for_node(self, node_id: str) -> None:
        pattern = f"compass:*:{node_id}"
        if self._redis is not None:
            keys = await self._redis.keys(pattern)
            if keys:
                await self._redis.delete(*keys)
            return
        for key in list(self._memory.keys()):
            if key.endswith(f":{node_id}"):
                self._memory.pop(key, None)


compass_cache = CompassCache()

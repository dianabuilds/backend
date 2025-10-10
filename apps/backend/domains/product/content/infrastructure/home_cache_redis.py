from __future__ import annotations

import json
import logging
from collections.abc import Mapping
from typing import Any

import redis.asyncio as redis  # type: ignore[import-untyped]
from redis.exceptions import RedisError  # type: ignore[import]

from domains.product.content.application.home_composer import HomeCache

logger = logging.getLogger(__name__)


class RedisHomeCache(HomeCache):
    def __init__(self, client: redis.Redis, *, default_ttl: int | None = None) -> None:
        self._client = client
        self._default_ttl = default_ttl

    async def get(self, key: str) -> Mapping[str, Any] | None:
        try:
            raw = await self._client.get(key)
        except RedisError as exc:
            logger.warning(
                "home.redis_cache_get_failed", extra={"key": key}, exc_info=exc
            )
            return None
        if raw is None:
            return None
        if isinstance(raw, bytes):
            try:
                raw = raw.decode("utf-8")
            except UnicodeDecodeError:
                raw = raw.decode("utf-8", errors="ignore")
        try:
            payload = json.loads(raw)
        except (TypeError, ValueError, json.JSONDecodeError) as exc:
            logger.debug("home.redis_cache_corrupted", extra={"key": key}, exc_info=exc)
            return None
        if isinstance(payload, Mapping):
            return dict(payload)
        return None

    async def set(
        self, key: str, value: Mapping[str, Any], *, ttl: int | None = None
    ) -> None:
        ttl_seconds = ttl if ttl is not None else self._default_ttl
        try:
            serialized = json.dumps(dict(value))
        except (TypeError, ValueError) as exc:
            logger.warning(
                "home.redis_cache_serialize_failed", extra={"key": key}, exc_info=exc
            )
            return
        try:
            await self._client.set(key, serialized, ex=ttl_seconds)
        except RedisError as exc:
            logger.warning(
                "home.redis_cache_set_failed", extra={"key": key}, exc_info=exc
            )

    async def invalidate(self, key: str) -> None:
        try:
            await self._client.delete(key)
        except RedisError as exc:
            logger.warning(
                "home.redis_cache_delete_failed", extra={"key": key}, exc_info=exc
            )


__all__ = ["RedisHomeCache"]

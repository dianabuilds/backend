from __future__ import annotations

import asyncio
import json
import logging
import time
from dataclasses import asdict, dataclass
from typing import Any

try:  # pragma: no cover - optional dependency
    import redis.asyncio as redis  # type: ignore[import-untyped]
    from redis.exceptions import RedisError  # type: ignore[import]
except ImportError:  # pragma: no cover - optional dependency
    redis = None  # type: ignore[assignment]
    RedisError = Exception  # type: ignore[misc,assignment]

from domains.product.nodes.application.ports import NodeCache, NodeDTO

logger = logging.getLogger(__name__)


@dataclass(slots=True)
class NodeCacheConfig:
    ttl_seconds: int = 300
    max_entries: int = 5000
    namespace: str = "product:nodes:v1"


def _serialize_dto(dto: NodeDTO) -> str:
    payload = asdict(dto)
    return json.dumps(payload, ensure_ascii=False, separators=(",", ":"))


def _deserialize_dto(raw: Any) -> NodeDTO | None:
    if raw is None:
        return None
    if isinstance(raw, bytes):
        raw = raw.decode("utf-8")
    try:
        data = json.loads(raw)
    except (TypeError, ValueError, json.JSONDecodeError):
        return None
    if not isinstance(data, dict):
        return None
    try:
        return NodeDTO(**data)
    except TypeError:
        return None


class RedisNodeCache(NodeCache):
    def __init__(
        self, client: redis.Redis, config: NodeCacheConfig | None = None
    ) -> None:
        if redis is None:
            raise RuntimeError("redis_asyncio_required")
        self._client = client
        self._config = config or NodeCacheConfig()

    def _key_id(self, node_id: int) -> str:
        return f"{self._config.namespace}:id:{int(node_id)}"

    def _key_slug(self, slug: str) -> str:
        return f"{self._config.namespace}:slug:{slug}".lower()

    async def get(self, node_id: int) -> NodeDTO | None:
        try:
            raw = await self._client.get(self._key_id(node_id))
        except RedisError as exc:  # pragma: no cover - network error
            logger.debug(
                "node_cache_redis_get_failed", extra={"node_id": node_id}, exc_info=exc
            )
            return None
        return _deserialize_dto(raw)

    async def get_by_slug(self, slug: str) -> NodeDTO | None:
        try:
            raw = await self._client.get(self._key_slug(slug))
        except RedisError as exc:  # pragma: no cover - network error
            logger.debug(
                "node_cache_redis_get_slug_failed", extra={"slug": slug}, exc_info=exc
            )
            return None
        return _deserialize_dto(raw)

    async def set(self, dto: NodeDTO) -> None:
        payload = _serialize_dto(dto)
        ttl = self._config.ttl_seconds if self._config.ttl_seconds > 0 else None
        try:
            await self._client.set(self._key_id(dto.id), payload, ex=ttl)
            if dto.slug:
                await self._client.set(self._key_slug(dto.slug), payload, ex=ttl)
        except RedisError as exc:  # pragma: no cover
            logger.debug(
                "node_cache_redis_set_failed", extra={"node_id": dto.id}, exc_info=exc
            )

    async def invalidate(self, node_id: int, slug: str | None = None) -> None:
        keys = [self._key_id(node_id)]
        if slug:
            keys.append(self._key_slug(slug))
        else:
            cached = await self.get(node_id)
            if cached and cached.slug:
                keys.append(self._key_slug(cached.slug))
        try:
            await self._client.delete(*keys)
        except RedisError as exc:  # pragma: no cover
            logger.debug(
                "node_cache_redis_delete_failed",
                extra={"node_id": node_id},
                exc_info=exc,
            )


class InMemoryNodeCache(NodeCache):
    def __init__(self, config: NodeCacheConfig | None = None) -> None:
        cfg = config or NodeCacheConfig()
        self._ttl = cfg.ttl_seconds
        self._max_entries = max(cfg.max_entries, 0)
        self._store: dict[int, tuple[float | None, str]] = {}
        self._slug_index: dict[str, int] = {}
        self._lock = asyncio.Lock()

    async def get(self, node_id: int) -> NodeDTO | None:
        async with self._lock:
            entry = self._store.get(int(node_id))
            if entry is None:
                return None
            expires_at, payload = entry
            if expires_at is not None and expires_at < time.monotonic():
                self._delete_locked(node_id)
                return None
        return _deserialize_dto(payload)

    async def get_by_slug(self, slug: str) -> NodeDTO | None:
        slug_key = slug.lower()
        async with self._lock:
            node_id = self._slug_index.get(slug_key)
        if node_id is None:
            return None
        return await self.get(node_id)

    async def set(self, dto: NodeDTO) -> None:
        payload = _serialize_dto(dto)
        expires_at = (
            time.monotonic() + self._ttl if self._ttl and self._ttl > 0 else None
        )
        async with self._lock:
            self._store[int(dto.id)] = (expires_at, payload)
            if dto.slug:
                self._slug_index[dto.slug.lower()] = int(dto.id)
            self._prune_locked()
            self._evict_locked()

    async def invalidate(self, node_id: int, slug: str | None = None) -> None:
        slug_key = slug.lower() if slug else None
        async with self._lock:
            if slug_key is None:
                entry = self._store.get(int(node_id))
                if entry is not None:
                    cached = _deserialize_dto(entry[1])
                    if cached and cached.slug:
                        slug_key = cached.slug.lower()
            self._delete_locked(node_id)
            if slug_key:
                self._slug_index.pop(slug_key, None)

    def _delete_locked(self, node_id: int) -> None:
        entry = self._store.pop(int(node_id), None)
        if entry is None:
            return
        cached = _deserialize_dto(entry[1])
        if cached and cached.slug:
            self._slug_index.pop(cached.slug.lower(), None)

    def _prune_locked(self) -> None:
        if not self._store:
            return
        now = time.monotonic()
        expired = [
            key
            for key, (expires_at, _) in self._store.items()
            if expires_at and expires_at < now
        ]
        for key in expired:
            self._delete_locked(key)

    def _evict_locked(self) -> None:
        if self._max_entries and len(self._store) > self._max_entries:
            # remove oldest items based on expiry or insertion order
            to_remove = len(self._store) - self._max_entries
            for key in list(self._store.keys()):
                self._delete_locked(key)
                to_remove -= 1
                if to_remove <= 0:
                    break


__all__ = ["NodeCacheConfig", "RedisNodeCache", "InMemoryNodeCache"]

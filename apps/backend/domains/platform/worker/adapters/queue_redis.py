from __future__ import annotations

import logging
from collections.abc import Sequence
from datetime import UTC, datetime
from typing import Any
from uuid import UUID

try:
    import redis.asyncio as aioredis  # type: ignore[import-untyped]
except ImportError:  # pragma: no cover - optional dependency
    aioredis = None  # type: ignore[assignment]

try:
    from redis.exceptions import RedisError  # type: ignore[import-untyped]
except ImportError:  # pragma: no cover - optional dependency
    RedisError = Exception  # type: ignore[misc, assignment]


logger = logging.getLogger(__name__)


class RedisWorkerQueue:
    """Sorted-set based queue for worker jobs (lower score dequeued first)."""

    def __init__(self, client: Any, *, key: str = "worker:jobs") -> None:
        self._client = client
        self._key = key

    async def push(self, job_id: UUID, priority: int) -> None:
        score = self._score(priority)
        await self._client.zadd(self._key, {str(job_id): score})

    async def push_many(self, pairs: Sequence[tuple[UUID, int]]) -> None:
        if not pairs:
            return
        mapping = {
            str(job_id): self._score(priority, offset=index)
            for index, (job_id, priority) in enumerate(pairs)
        }
        await self._client.zadd(self._key, mapping)

    async def pop_many(self, limit: int) -> list[UUID]:
        if limit <= 0:
            return []
        items = await self._client.zpopmin(self._key, limit)
        return [UUID(value) for value, _score in items]

    async def close(self) -> None:  # pragma: no cover - optional cleanup
        try:
            await self._client.close()
        except (RedisError, RuntimeError) as exc:
            logger.debug("redis queue close failed on close(): %s", exc)
            return
        try:
            await self._client.wait_closed()
        except (RedisError, RuntimeError) as exc:
            logger.debug("redis queue close failed on wait_closed(): %s", exc)

    @staticmethod
    def _score(priority: int, *, offset: int = 0) -> float:
        base = max(0, int(priority)) * 1_000_000_000
        now = int(datetime.now(UTC).timestamp() * 1_000_000)
        return float(base + now + offset)


__all__ = ["RedisWorkerQueue"]

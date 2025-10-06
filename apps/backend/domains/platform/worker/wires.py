from __future__ import annotations

import logging
from dataclasses import dataclass

from packages.core.config import Settings, load_settings, to_async_dsn

from .adapters.queue_redis import RedisWorkerQueue
from .adapters.sql.jobs import SQLWorkerJobRepository
from .application.service import WorkerQueueService

logger = logging.getLogger(__name__)


@dataclass(slots=True)
class WorkerContainer:
    repo: SQLWorkerJobRepository
    queue: object | None
    service: WorkerQueueService


def build_container(settings: Settings | None = None) -> WorkerContainer:
    s = settings or load_settings()
    async_dsn = to_async_dsn(s.database_url)
    repo = SQLWorkerJobRepository(async_dsn)
    queue = None
    redis_url = getattr(s, "redis_url", None)
    if redis_url:
        try:
            import redis.asyncio as aioredis  # type: ignore[import-untyped]
            from redis.exceptions import RedisError  # type: ignore[import-untyped]
        except ImportError as exc:
            logger.warning("worker redis queue disabled: %s", exc)
        else:
            try:
                client = aioredis.from_url(str(redis_url), decode_responses=False)
                queue = RedisWorkerQueue(client)
            except (RedisError, ValueError, TypeError) as exc:
                logger.error("worker redis queue init failed: %s", exc)
    service = WorkerQueueService(repo, queue=queue)
    return WorkerContainer(repo=repo, queue=queue, service=service)


__all__ = ["WorkerContainer", "build_container"]

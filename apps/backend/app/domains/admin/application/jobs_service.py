from __future__ import annotations

import json

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.models.background_job_history import BackgroundJobHistory
from app.providers.cache import cache as shared_cache
from app.providers.redis_utils import create_async_redis


class JobsService:
    @staticmethod
    async def record_run(
        db: AsyncSession,
        name: str,
        status: str,
        log_url: str | None = None,
    ) -> BackgroundJobHistory:
        job = BackgroundJobHistory(name=name, status=status, log_url=log_url)
        db.add(job)
        await db.commit()
        await db.refresh(job)
        return job

    @staticmethod
    async def get_recent(db: AsyncSession, limit: int = 10) -> list[dict]:
        cache_key = f"admin:jobs:recent:{limit}"
        cached = await shared_cache.get(cache_key)
        if cached:
            return json.loads(cached)
        result = await db.execute(
            select(BackgroundJobHistory)
            .order_by(BackgroundJobHistory.started_at.desc())
            .limit(limit)
        )
        jobs = [
            {
                "id": str(j.id),
                "name": j.name,
                "status": j.status,
                "log_url": j.log_url,
                "started_at": j.started_at.isoformat(),
                "finished_at": j.finished_at.isoformat() if j.finished_at else None,
            }
            for j in result.scalars().all()
        ]
        await shared_cache.set(cache_key, json.dumps(jobs), 120)
        return jobs

    @staticmethod
    async def get_queue_stats() -> dict[str, dict[str, int]]:
        """Return pending and active job counts for each BullMQ queue.

        The implementation inspects Redis keys used by BullMQ.  For every
        ``<queue>:meta`` key it calculates sizes of ``<queue>:wait`` and
        ``<queue>:active`` lists.  If async processing is disabled or the
        broker URL is not a Redis DSN an empty mapping is returned.
        """

        broker_url = settings.queue_broker_url
        if not (settings.async_enabled and broker_url):
            return {}

        if not broker_url.startswith("redis"):
            return {}

        client = create_async_redis(broker_url, decode_responses=True)
        try:
            queues: dict[str, dict[str, int]] = {}
            cursor = 0
            while True:
                cursor, keys = await client.scan(cursor, match="*:meta", count=100)
                for key in keys:
                    if isinstance(key, bytes):
                        key = key.decode()
                    queue = key[:-5] if key.endswith(":meta") else key
                    pending = await client.llen(f"{queue}:wait")
                    active = await client.llen(f"{queue}:active")
                    queues[queue] = {"pending": pending, "active": active}
                if cursor == 0:
                    break
            return queues
        finally:  # pragma: no cover - close even if scan fails
            await client.aclose()

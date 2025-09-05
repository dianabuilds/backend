from __future__ import annotations

import asyncio
from uuid import UUID

import redis
from rq import Queue

from app.core.config import settings
from app.domains.notifications.application.broadcast_service import run_campaign
from app.providers.db.session import get_session_factory

_redis_conn: redis.Redis | None = None
_campaign_queue: Queue | None = None
if settings.redis_url:
    if settings.redis_url.startswith("fakeredis://"):
        import fakeredis

        _redis_conn = fakeredis.FakeRedis()
    else:
        _redis_conn = redis.from_url(settings.redis_url)
    _campaign_queue = Queue("notifications", connection=_redis_conn)


def run_campaign_job(campaign_id: str) -> None:
    async def _inner() -> None:
        session_factory = get_session_factory()
        async with session_factory() as session:
            await run_campaign(session, UUID(campaign_id))

    asyncio.run(_inner())


def enqueue_campaign(campaign_id: UUID) -> None:
    if _campaign_queue is None:
        raise RuntimeError("Redis not configured")
    _campaign_queue.enqueue(run_campaign_job, str(campaign_id))


campaign_queue = _campaign_queue

__all__ = ["enqueue_campaign", "campaign_queue", "run_campaign_job"]

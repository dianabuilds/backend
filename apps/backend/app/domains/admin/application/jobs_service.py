from __future__ import annotations

import json

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.cache import cache as shared_cache
from app.models.background_job_history import BackgroundJobHistory


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

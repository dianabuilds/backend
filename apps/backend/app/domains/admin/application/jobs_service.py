from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

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
    async def get_recent(db: AsyncSession, limit: int = 10) -> list[BackgroundJobHistory]:
        result = await db.execute(
            select(BackgroundJobHistory)
            .order_by(BackgroundJobHistory.started_at.desc())
            .limit(limit)
        )
        return list(result.scalars().all())

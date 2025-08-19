from __future__ import annotations

from datetime import datetime
from typing import Any, Optional
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

from app.models.ai_generation import GenerationJob, JobStatus


async def enqueue_generation_job(
    db: AsyncSession,
    *,
    created_by: Optional[UUID],
    params: dict[str, Any],
    provider: str | None = None,
    model: str | None = None,
    reuse: bool = True,
) -> GenerationJob:
    """Создать задание на генерацию ИИ‑квеста и поставить в очередь.
    Если reuse=True и уже есть завершённая задача с идентичными параметрами — создаём
    мгновенно завершённую job, переиспользуя result_quest_id/cost/token_usage.
    """
    if reuse:
        # Ищем последнюю завершённую задачу с такими же параметрами
        res = await db.execute(
            select(GenerationJob)
                .where(GenerationJob.status == JobStatus.completed, GenerationJob.params == params)
                .order_by(GenerationJob.finished_at.desc())
        )
        cached = res.scalars().first()
        if cached:
            job = GenerationJob(
                created_by=created_by,
                provider=provider or cached.provider,
                model=model or cached.model,
                params=params,
                status=JobStatus.completed,
                created_at=datetime.utcnow(),
                started_at=datetime.utcnow(),
                finished_at=datetime.utcnow(),
                result_quest_id=cached.result_quest_id,
                result_version_id=cached.result_version_id,
                cost=cached.cost,
                token_usage=cached.token_usage,
                reused=True,
                error=None,
            )
            db.add(job)
            await db.flush()
            return job

    # Обычная постановка в очередь
    job = GenerationJob(
        created_by=created_by,
        provider=provider,
        model=model,
        params=params,
        status=JobStatus.queued,
    )
    db.add(job)
    await db.flush()  # чтобы получить id
    return job

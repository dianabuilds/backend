from __future__ import annotations

from datetime import datetime, timedelta

from sqlalchemy import func, update
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

from app.domains.ai.infrastructure.models.generation_models import GenerationJob


async def recover_stuck_generation_jobs(db: AsyncSession, *, ttl_seconds: int = 3600) -> int:
    """
    Помечает 'running' задачи как 'failed', если они не обновлялись дольше, чем ttl_seconds.
    Ориентируется на updated_at, затем started_at, затем created_at (fallback).
    Возвращает количество помеченных задач.
    """
    now = datetime.utcnow()
    threshold = now - timedelta(seconds=max(1, int(ttl_seconds)))
    # Выберем кандидатов (running и старая метка времени)
    # Используем COALESCE(updated_at, started_at, created_at)
    stale_expr = func.coalesce(
        GenerationJob.updated_at, GenerationJob.started_at, GenerationJob.created_at
    )
    res = await db.execute(
        select(GenerationJob.id).where(
            GenerationJob.status == "running",
            stale_expr < threshold,
        )
    )
    ids = [row for row in res.scalars().all()]
    if not ids:
        return 0
    # Помечаем как failed с ошибкой и finished_at = now
    await db.execute(
        update(GenerationJob)
        .where(GenerationJob.id.in_(ids))
        .values(status="failed", finished_at=now, error="stuck_timeout")
    )
    await db.commit()
    return len(ids)

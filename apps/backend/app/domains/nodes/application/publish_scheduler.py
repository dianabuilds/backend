from __future__ import annotations

from collections.abc import Iterable
from datetime import UTC, datetime

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.domains.nodes.application.node_service import NodeService
from app.domains.nodes.models import NodeItem, NodePublishJob


async def process_due_jobs(db: AsyncSession, *, limit: int = 50) -> dict:
    """
    Выполнить отложенные публикации, срок которых наступил.
    Возвращает отчёт о выполненных заданиях.
    """
    now = datetime.now(UTC).replace(tzinfo=None)  # БД хранит naive UTC
    res = await db.execute(
        select(NodePublishJob)
        .where(NodePublishJob.status == "pending", NodePublishJob.scheduled_at <= now)
        .limit(limit)
    )
    jobs: Iterable[NodePublishJob] = list(res.scalars().all())
    svc = NodeService(db)
    executed: list[str] = []
    failed: list[str] = []

    for job in jobs:
        try:
            item: NodeItem | None = await db.get(NodeItem, job.content_id)
            if not item:
                job.status = "failed"
                job.error = "Content not found"
                failed.append(str(job.id))
                continue
            # Публикация согласно access
            await svc.publish(item.id, actor_id=job.created_by_user_id or item.created_by_user_id, access=job.access)
            job.status = "done"
            job.executed_at = datetime.utcnow()
            executed.append(str(job.id))
        except Exception as e:
            job.status = "failed"
            job.error = str(e)
            failed.append(str(job.id))
    await db.commit()
    return {"executed": executed, "failed": failed}

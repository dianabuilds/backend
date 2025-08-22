from __future__ import annotations

from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy import func

from app.api.deps import admin_required
from app.db.session import get_db
from app.domains.ai.infrastructure.models.generation_models import GenerationJob
from app.domains.common.schemas.paginated import Paginated

router = APIRouter(prefix="/admin/ai/quests", tags=["admin-ai-quests"])


@router.get("/jobs_paged", response_model=Paginated[dict])
async def list_jobs_paged(
    page: int = Query(1, ge=1),
    per_page: int = Query(20, ge=1, le=100),
    status: Optional[str] = Query(None, pattern="^(queued|running|completed|failed|canceled)$"),
    db: AsyncSession = Depends(get_db),
    _admin: Any = Depends(admin_required),
) -> Dict[str, Any]:
    base = select(GenerationJob)
    if status:
        base = base.where(GenerationJob.status == status)
    total_q = select(func.count()).select_from(base.subquery())
    total_res = await db.execute(total_q)
    total = int(total_res.scalar() or 0)

    offset = (page - 1) * per_page
    q = base.order_by(GenerationJob.created_at.desc()).offset(offset).limit(per_page)
    res = await db.execute(q)
    rows = res.scalars().all()

    items: List[Dict[str, Any]] = []
    for j in rows:
        items.append(
            {
                "id": str(j.id),
                "status": j.status,
                "created_at": j.created_at.isoformat() if j.created_at else None,
                "started_at": j.started_at.isoformat() if j.started_at else None,
                "finished_at": j.finished_at.isoformat() if j.finished_at else None,
                "created_by": str(j.created_by) if j.created_by else None,
                "provider": j.provider,
                "model": j.model,
                "params": j.params,
                "result_quest_id": str(j.result_quest_id) if j.result_quest_id else None,
                "result_version_id": str(j.result_version_id) if j.result_version_id else None,
                "cost": float(j.cost) if j.cost is not None else None,
                "token_usage": j.token_usage,
                "reused": bool(j.reused),
                "progress": int(j.progress or 0),
                "logs": j.logs or None,
                "error": j.error,
            }
        )

    return {"page": page, "per_page": per_page, "total": total, "items": items}

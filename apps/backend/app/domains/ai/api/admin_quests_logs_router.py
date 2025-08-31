from __future__ import annotations

from typing import Annotated, Any

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

from app.api.deps import admin_required
from app.core.db.session import get_db
from app.domains.ai.infrastructure.models.generation_models import GenerationJobLog

router = APIRouter(prefix="/admin/ai/quests", tags=["admin-ai-quests"])


@router.get("/jobs/{job_id}/logs")
async def get_generation_job_logs(
    job_id: str,
    db: Annotated[AsyncSession, Depends(get_db)] = ...,
    _admin: Annotated[Any, Depends(admin_required)] = ...,
    limit: Annotated[int, Query(ge=1, le=1000)] = 200,
    clip: Annotated[int, Query(ge=512, le=200000)] = 5000,
) -> list[dict[str, Any]]:
    try:
        q = (
            select(GenerationJobLog)
            .where(GenerationJobLog.job_id == job_id)
            .order_by(GenerationJobLog.created_at.asc())
            .limit(limit)
        )
        res = await db.execute(q)
        rows = res.scalars().all()
        out: list[dict[str, Any]] = []
        for r in rows:
            prompt = (r.prompt or "")[:clip] if r.prompt else None
            raw = (r.raw_response or "")[:clip] if r.raw_response else None
            out.append(
                {
                    "stage": r.stage,
                    "provider": r.provider,
                    "model": r.model,
                    "prompt": prompt,
                    "raw_response": raw,
                    "usage": r.usage,
                    "cost": r.cost,
                    "status": r.status,
                    "created_at": r.created_at.isoformat() if r.created_at else None,
                }
            )
        return out
    except Exception as e:
        raise HTTPException(
            status_code=404, detail=f"Logs not found or unavailable: {e}"
        ) from e

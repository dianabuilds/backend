from __future__ import annotations

from typing import Annotated, Any

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

from app.api.deps import admin_required
from app.domains.ai.infrastructure.models.generation_models import (
    GenerationJob,
    GenerationJobLog,
)
from app.providers.db.session import get_db

router = APIRouter(prefix="/admin/ai/quests", tags=["admin-ai-quests"])


@router.get("/jobs/{job_id}/details")
async def get_generation_job_details(
    job_id: str,
    db: Annotated[AsyncSession, Depends(get_db)] = ...,
    _admin: Annotated[Any, Depends(admin_required)] = ...,
) -> dict[str, Any]:
    res = await db.execute(select(GenerationJob).where(GenerationJob.id == job_id))
    job: GenerationJob | None = res.scalars().first()
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")

    logs: list[dict[str, Any]] = []
    try:
        r = await db.execute(
            select(GenerationJobLog)
            .where(GenerationJobLog.job_id == job_id)
            .order_by(GenerationJobLog.created_at.asc())
        )
        for row in r.scalars().all():
            logs.append(
                {
                    "stage": row.stage,
                    "provider": row.provider,
                    "model": row.model,
                    "prompt": row.prompt,
                    "raw_response": row.raw_response,
                    "usage": row.usage,
                    "cost": row.cost,
                    "status": row.status,
                    "created_at": (
                        row.created_at.isoformat() if row.created_at else None
                    ),
                }
            )
    except Exception:
        logs = []

    agg_prompt = 0
    agg_completion = 0
    agg_cost = 0.0
    for log_entry in logs:
        u = log_entry.get("usage") or {}
        try:
            agg_prompt += int(u.get("prompt", 0))
            agg_completion += int(u.get("completion", 0))
        except Exception:
            pass
        try:
            agg_cost += float(log_entry.get("cost") or 0.0)
        except Exception:
            pass

    details = {
        "job": {
            "id": str(job.id),
            "status": job.status,
            "created_at": job.created_at.isoformat() if job.created_at else None,
            "started_at": job.started_at.isoformat() if job.started_at else None,
            "finished_at": job.finished_at.isoformat() if job.finished_at else None,
            "created_by": (
                str(job.created_by) if getattr(job, "created_by", None) else None
            ),
            "provider": job.provider,
            "model": job.model,
            "params": job.params,
            "result_quest_id": (
                str(job.result_quest_id) if job.result_quest_id else None
            ),
            "result_version_id": (
                str(job.result_version_id) if job.result_version_id else None
            ),
            "cost": float(job.cost) if job.cost is not None else None,
            "token_usage": job.token_usage,
            "reused": bool(job.reused),
            "progress": int(job.progress or 0),
            "logs_inline": job.logs or None,
            "error": job.error,
        },
        "stage_logs": logs,
        "aggregates": {
            "prompt_tokens": agg_prompt,
            "completion_tokens": agg_completion,
            "total_tokens": agg_prompt + agg_completion,
            "cost": agg_cost,
        },
    }
    return details

from __future__ import annotations

from typing import Any

from fastapi import APIRouter, Depends

from app.domains.telemetry.application.worker_metrics_facade import worker_metrics
from app.security import ADMIN_AUTH_RESPONSES, require_admin_role

router = APIRouter(
    prefix="/admin/ai/quests", tags=["admin-ai-quests"], responses=ADMIN_AUTH_RESPONSES
)


@router.get("/stats")
async def get_ai_worker_stats(_=Depends(require_admin_role())) -> dict[str, Any]:
    """
    Сводка по задачам/стадиям генерации: счётчики, среднее время, стоимость, токены.
    """
    try:
        return worker_metrics.snapshot()
    except Exception:
        return {
            "jobs": {},
            "job_avg_ms": 0.0,
            "cost_usd_total": 0.0,
            "tokens": {"prompt": 0, "completion": 0},
            "stages": {},
        }

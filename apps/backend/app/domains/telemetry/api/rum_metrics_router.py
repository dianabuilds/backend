from __future__ import annotations

import logging
from typing import Annotated, Any

from fastapi import APIRouter, Depends, Query, Request

from app.api.deps import admin_required
from app.domains.telemetry.application.rum_service import rum_service
from app.domains.users.infrastructure.models.user import User

router = APIRouter(tags=["metrics"])
admin_router = APIRouter(prefix="/admin/telemetry", tags=["admin-telemetry"])

log = logging.getLogger("rum")


@router.post("/metrics/rum")
async def rum_metrics(request: Request) -> dict[str, Any]:
    """
    Приёмник простых RUM-событий с фронтенда.
    Тело: { event: str, ts: int, url: str, data: any }
    """
    try:
        payload = await request.json()
    except Exception:
        payload = {"parse_error": True}
    log.info("RUM %s", payload)
    if isinstance(payload, dict):
        await rum_service.record(payload)
    return {"ok": True}


@admin_router.get("/rum")
async def list_rum_events(
    _admin: Annotated[User, Depends(admin_required)],
    event: Annotated[str | None, Query(max_length=100)] = None,
    url: Annotated[str | None, Query(max_length=500)] = None,
    offset: Annotated[int, Query(ge=0)] = 0,
    limit: Annotated[int, Query(ge=1, le=1000)] = 200,
) -> list[dict[str, Any]]:
    """
    Админ: последние RUM-события (по убыванию времени).
    """
    return await rum_service.list_events(event=event, url=url, offset=offset, limit=limit)


@admin_router.get("/rum/summary")
async def rum_summary(
    _admin: Annotated[User, Depends(admin_required)],
    window: Annotated[int, Query(ge=1, le=1000)] = 500,
) -> dict[str, Any]:
    """
    Админ: сводка по последним событиям.
    - counts по event
    - средняя длительность login_attempt.dur_ms
    - навигационные тайминги (средние по окну): ttfb, domContentLoaded, loadEvent
    """
    return await rum_service.summary(window)

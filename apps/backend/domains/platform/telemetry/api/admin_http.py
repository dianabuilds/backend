from __future__ import annotations

from typing import Any

from fastapi import APIRouter, Depends, Query, Request

try:
    from fastapi_limiter.depends import RateLimiter  # type: ignore
except Exception:  # pragma: no cover
    RateLimiter = None  # type: ignore

from apps.backend import get_container
from domains.platform.iam.security import require_admin


def make_router() -> APIRouter:
    router = APIRouter(
        prefix="/v1/admin/telemetry", tags=["admin-telemetry"]
    )  # guarded per-route

    @router.get(
        "/rum",
        dependencies=(
            [Depends(RateLimiter(times=60, seconds=60))] if RateLimiter else []
        ),
    )
    async def list_rum_events(
        req: Request,
        _admin: None = Depends(require_admin),
        event: str | None = Query(default=None, max_length=100),
        url: str | None = Query(default=None, max_length=500),
        offset: int = Query(default=0, ge=0),
        limit: int = Query(default=200, ge=1, le=1000),
    ) -> list[dict[str, Any]]:
        container = get_container(req)
        return await container.telemetry.rum_service.list_events(
            event=event, url=url, offset=offset, limit=limit
        )

    @router.get(
        "/rum/summary",
        dependencies=(
            [Depends(RateLimiter(times=60, seconds=60))] if RateLimiter else []
        ),
    )
    async def rum_summary(
        req: Request,
        window: int = Query(default=500, ge=1, le=1000),
        _admin: None = Depends(require_admin),
    ) -> dict[str, Any]:
        container = get_container(req)
        return await container.telemetry.rum_service.summary(window)

    return router

from __future__ import annotations

from typing import Any

from fastapi import APIRouter, Depends, Query, Request

try:
    from fastapi_limiter.depends import RateLimiter  # type: ignore
except Exception:  # pragma: no cover
    RateLimiter = None  # type: ignore

from apps.backendDDD.app.api_gateway.routers import get_container
from apps.backendDDD.domains.platform.iam.security import csrf_protect, require_admin


def make_router() -> APIRouter:
    router = APIRouter(prefix="/v1/audit", tags=["audit"])

    @router.get("")
    async def list_events(
        req: Request,
        limit: int = Query(default=100, ge=1, le=1000),
        _admin: None = Depends(require_admin),
    ) -> dict[str, Any]:
        c = get_container(req)
        items = await c.audit.repo.list(limit=int(limit))
        return {"items": items}

    @router.post("")
    @router.post(
        "",
        dependencies=(
            [Depends(RateLimiter(times=20, seconds=60))] if RateLimiter else []
        ),
    )
    async def log_event(
        req: Request,
        payload: dict[str, Any],
        _admin: None = Depends(require_admin),
        _csrf: None = Depends(csrf_protect),
    ) -> dict[str, Any]:
        c = get_container(req)
        p = payload or {}
        await c.audit.service.log(
            actor_id=p.get("actor_id"),
            action=str(p.get("action", "")),
            resource_type=p.get("resource_type"),
            resource_id=p.get("resource_id"),
            before=p.get("before"),
            after=p.get("after"),
            ip=p.get("ip"),
            user_agent=p.get("user_agent"),
            reason=p.get("reason"),
            extra=p.get("extra"),
        )
        return {"ok": True}

    return router

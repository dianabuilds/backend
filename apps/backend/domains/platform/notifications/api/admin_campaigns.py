from __future__ import annotations

from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Query, Request

try:
    from fastapi_limiter.depends import RateLimiter  # type: ignore
except Exception:  # pragma: no cover
    RateLimiter = None  # type: ignore

from apps.backend import get_container
from domains.platform.iam.security import csrf_protect, require_admin


def make_router() -> APIRouter:
    router = APIRouter(prefix="/v1/notifications/admin", tags=["admin-notifications"])

    @router.get(
        "/campaigns",
        dependencies=(
            [Depends(RateLimiter(times=60, seconds=60))] if RateLimiter else []
        ),
    )
    async def list_campaigns(
        req: Request,
        limit: int = Query(default=50, ge=1, le=200),
        offset: int = Query(default=0, ge=0),
        _admin: None = Depends(require_admin),
    ) -> dict[str, Any]:
        c = get_container(req)
        items = await c.notifications.campaigns.list(limit=limit, offset=offset)
        return {"items": items}

    @router.post(
        "/campaigns",
        dependencies=(
            [Depends(RateLimiter(times=10, seconds=60))] if RateLimiter else []
        ),
    )
    async def upsert_campaign(
        req: Request,
        body: dict[str, Any],
        _admin: None = Depends(require_admin),
        _csrf: None = Depends(csrf_protect),
    ) -> dict[str, Any]:
        c = get_container(req)
        if (
            not body.get("title")
            or not body.get("message")
            or not body.get("created_by")
        ):
            raise HTTPException(
                status_code=400, detail="title,message,created_by required"
            )
        res = await c.notifications.campaigns.upsert(body)
        return {"campaign": res}

    @router.delete(
        "/campaigns/{campaign_id}",
        dependencies=(
            [Depends(RateLimiter(times=10, seconds=60))] if RateLimiter else []
        ),
    )
    async def delete_campaign(
        req: Request,
        campaign_id: str,
        _admin: None = Depends(require_admin),
        _csrf: None = Depends(csrf_protect),
    ) -> dict[str, Any]:
        c = get_container(req)
        await c.notifications.campaigns.delete(campaign_id)
        return {"ok": True}

    return router

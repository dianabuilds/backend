from __future__ import annotations

from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Query, Request

try:
    from fastapi_limiter.depends import RateLimiter  # type: ignore
except Exception:  # pragma: no cover
    RateLimiter = None  # type: ignore

from apps.backendDDD.app.api_gateway.routers import get_container
from apps.backendDDD.domains.platform.iam.security import (
    csrf_protect,
    get_current_user,
    require_admin,
)


def make_router() -> APIRouter:
    router = APIRouter(prefix="/v1/notifications", tags=["notifications"])

    @router.get(
        "",
        dependencies=(
            [Depends(RateLimiter(times=60, seconds=60))] if RateLimiter else []
        ),
    )
    async def list_my_notifications(
        req: Request,
        limit: int = Query(default=50, ge=1, le=200),
        offset: int = Query(default=0, ge=0),
        claims=Depends(get_current_user),
    ) -> dict[str, Any]:
        c = get_container(req)
        user_id = str(claims.get("sub"))
        items = await c.notifications.repo.list_for_user(
            user_id, limit=limit, offset=offset
        )
        return {"items": items}

    @router.post(
        "/read/{notif_id}",
        dependencies=(
            [Depends(RateLimiter(times=60, seconds=60))] if RateLimiter else []
        ),
    )
    async def mark_read(
        req: Request,
        notif_id: str,
        claims=Depends(get_current_user),
        _csrf: None = Depends(csrf_protect),
    ) -> dict[str, Any]:
        c = get_container(req)
        user_id = str(claims.get("sub"))
        ok = await c.notifications.repo.mark_read(user_id, notif_id)
        if not ok:
            raise HTTPException(status_code=404, detail="not_found")
        return {"ok": True}

    # Admin send
    @router.post(
        "/admin/send",
        dependencies=(
            [Depends(RateLimiter(times=10, seconds=60))] if RateLimiter else []
        ),
    )
    async def admin_send(
        req: Request,
        body: dict[str, Any],
        _admin: None = Depends(require_admin),
        _csrf: None = Depends(csrf_protect),
    ) -> dict[str, Any]:
        c = get_container(req)
        user_id = str(body.get("user_id") or "")
        if not user_id:
            raise HTTPException(status_code=400, detail="user_id_required")
        title = str(body.get("title") or "")
        message = str(body.get("message") or "")
        type_ = str(body.get("type") or "system")
        placement = str(body.get("placement") or "inbox")
        dto = await c.notifications.notify.create_notification(
            user_id=user_id,
            title=title,
            message=message,
            type=type_,
            placement=placement,
        )
        return {"notification": dto}

    return router

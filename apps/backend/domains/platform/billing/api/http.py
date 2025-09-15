from __future__ import annotations

from typing import Any

from fastapi import APIRouter, Depends, Header, HTTPException, Request

try:
    from fastapi_limiter.depends import RateLimiter  # type: ignore
except Exception:  # pragma: no cover
    RateLimiter = None  # type: ignore

from apps.backend import get_container
from domains.platform.iam.security import (
    csrf_protect,
    get_current_user,
    require_admin,
)


def make_router() -> APIRouter:
    router = APIRouter(prefix="/v1/billing", tags=["billing"])

    @router.get("/plans")
    async def list_plans(req: Request) -> dict[str, Any]:
        c = get_container(req)
        plans = await c.billing.service.list_plans()
        return {"items": [p.__dict__ for p in plans]}

    @router.post(
        "/checkout",
        dependencies=(
            [Depends(RateLimiter(times=5, seconds=60))] if RateLimiter else []
        ),
    )
    async def checkout(
        req: Request,
        body: dict[str, Any],
        claims=Depends(get_current_user),
        _csrf: None = Depends(csrf_protect),
    ) -> dict[str, Any]:
        c = get_container(req)
        user_id = str(claims.get("sub"))
        plan_slug = str(body.get("plan"))
        if not plan_slug:
            raise HTTPException(status_code=400, detail="plan_required")
        res = await c.billing.service.checkout(user_id, plan_slug)
        return {"ok": True, "checkout": res.__dict__}

    @router.post("/webhook")
    async def webhook(
        req: Request, x_signature: str | None = Header(default=None)
    ) -> dict[str, Any]:
        c = get_container(req)
        payload = await req.body()
        return await c.billing.service.handle_webhook(payload, x_signature)

    @router.get("/subscriptions/me")
    async def my_subscription(
        req: Request, claims=Depends(get_current_user)
    ) -> dict[str, Any]:
        c = get_container(req)
        user_id = str(claims.get("sub"))
        sub = await c.billing.service.get_subscription_for_user(user_id)
        return {"subscription": sub}

    # Admin
    @router.post("/admin/plans")
    async def admin_upsert_plan(
        req: Request,
        body: dict[str, Any],
        _admin: None = Depends(require_admin),
        _csrf: None = Depends(csrf_protect),
    ) -> dict[str, Any]:
        c = get_container(req)
        plan = await c.billing.plans.upsert(body)
        return {"plan": plan.__dict__}

    @router.delete("/admin/plans/{plan_id}")
    async def admin_delete_plan(
        req: Request,
        plan_id: str,
        _admin: None = Depends(require_admin),
        _csrf: None = Depends(csrf_protect),
    ) -> dict[str, Any]:
        c = get_container(req)
        await c.billing.plans.delete(plan_id)
        return {"ok": True}

    return router

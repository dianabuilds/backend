from __future__ import annotations

from typing import Any

from fastapi import APIRouter, Depends

from apps.backendDDD.app.api_gateway.routers import get_container
from apps.backendDDD.domains.platform.iam.security import get_current_user


def make_router() -> APIRouter:
    router = APIRouter(prefix="/v1/premium", tags=["premium"])

    @router.get("/me/limits")
    async def my_limits(
        claims=Depends(get_current_user), container=Depends(get_container)
    ) -> dict[str, Any]:
        user_id = str(claims.get("sub") or "") if claims else ""
        plan = await container.premium_service.get_effective_plan_slug(user_id)
        stories = await container.premium_service.get_quota_status(
            user_id, quota_key="stories", scope="month"
        )
        return {"plan": plan, "limits": {"stories": {"month": stories}}}

    return router

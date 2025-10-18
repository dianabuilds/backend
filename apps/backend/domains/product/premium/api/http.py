from __future__ import annotations

from typing import Any

from fastapi import APIRouter, Depends

from apps.backend.app.api_gateway.routers import get_container
from domains.platform.iam.application.facade import get_current_user


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
        limits = {"stories": {"month": stories}, "month": {"stories": stories}}
        return {"plan": plan, "limits": limits}

    return router

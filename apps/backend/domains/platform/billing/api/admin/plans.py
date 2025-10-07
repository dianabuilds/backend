from __future__ import annotations

from typing import Any

from fastapi import APIRouter, Depends, HTTPException

from domains.platform.billing.application.use_cases.exceptions import (
    BillingUseCaseError,
)
from domains.platform.iam.security import csrf_protect, require_admin

from ..deps import get_actor_id, get_admin_plans_use_case


def register(router: APIRouter) -> None:
    @router.post("/admin/plans")
    async def admin_upsert_plan(
        body: dict[str, Any],
        use_case=Depends(get_admin_plans_use_case),
        actor_id=Depends(get_actor_id),
        _admin: None = Depends(require_admin),
        _csrf: None = Depends(csrf_protect),
    ) -> dict[str, Any]:
        try:
            return await use_case.upsert(payload=body, actor_id=actor_id)
        except BillingUseCaseError as exc:
            raise HTTPException(status_code=exc.status_code, detail=exc.detail) from exc

    @router.delete("/admin/plans/{plan_id}")
    async def admin_delete_plan(
        plan_id: str,
        use_case=Depends(get_admin_plans_use_case),
        _admin: None = Depends(require_admin),
        _csrf: None = Depends(csrf_protect),
    ) -> dict[str, Any]:
        try:
            return await use_case.delete(plan_id=plan_id)
        except BillingUseCaseError as exc:
            raise HTTPException(status_code=exc.status_code, detail=exc.detail) from exc

    @router.get("/admin/plans/all")
    async def admin_list_all_plans(
        use_case=Depends(get_admin_plans_use_case),
        _admin: None = Depends(require_admin),
    ) -> dict[str, Any]:
        return await use_case.list_all()

    @router.post("/admin/plans/bulk_limits")
    async def admin_bulk_limits(
        body: dict[str, Any],
        use_case=Depends(get_admin_plans_use_case),
        _admin: None = Depends(require_admin),
        _csrf: None = Depends(csrf_protect),
    ) -> dict[str, Any]:
        items = body.get("items") or []
        return await use_case.bulk_limits(items=items)

    @router.get("/admin/plans/{slug}/audit")
    async def admin_plan_audit(
        slug: str,
        limit: int = 100,
        use_case=Depends(get_admin_plans_use_case),
        _admin: None = Depends(require_admin),
    ) -> dict[str, Any]:
        return await use_case.audit(slug=slug, limit=limit)

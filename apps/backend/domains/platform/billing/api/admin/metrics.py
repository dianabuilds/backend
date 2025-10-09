from __future__ import annotations

from typing import Any

from fastapi import APIRouter, Depends, Query

from domains.platform.iam.security import csrf_protect, require_admin

from ..deps import get_admin_metrics_use_case


def register(router: APIRouter) -> None:
    @router.get("/summary")
    async def billing_summary(
        user_id: str = Query(..., description="User ID"),
        use_case=Depends(get_admin_metrics_use_case),
        _admin: None = Depends(require_admin),
    ) -> dict[str, Any]:
        return await use_case.summary(user_id=user_id)

    @router.get("/history")
    async def billing_history(
        user_id: str = Query(..., description="User ID"),
        limit: int = Query(20, ge=1, le=100),
        use_case=Depends(get_admin_metrics_use_case),
        _admin: None = Depends(require_admin),
    ) -> dict[str, Any]:
        return await use_case.history(user_id=user_id, limit=limit)

    @router.get("/admin/kpi")
    async def admin_kpi(
        use_case=Depends(get_admin_metrics_use_case),
        _admin: None = Depends(require_admin),
    ) -> dict[str, Any]:
        return await use_case.kpi()

    @router.get("/admin/metrics")
    async def admin_metrics(
        use_case=Depends(get_admin_metrics_use_case),
        _admin: None = Depends(require_admin),
    ) -> dict[str, Any]:
        return await use_case.metrics()

    @router.get("/admin/revenue_ts")
    async def admin_revenue_ts(
        days: int = 30,
        use_case=Depends(get_admin_metrics_use_case),
        _admin: None = Depends(require_admin),
    ) -> dict[str, Any]:
        return await use_case.revenue_ts(days=days)

    @router.get("/admin/crypto-config")
    async def get_crypto_config(
        use_case=Depends(get_admin_metrics_use_case),
        _admin: None = Depends(require_admin),
    ) -> dict[str, Any]:
        return await use_case.get_crypto_config()

    @router.post("/admin/crypto-config")
    async def set_crypto_config(
        body: dict[str, Any],
        use_case=Depends(get_admin_metrics_use_case),
        _admin: None = Depends(require_admin),
        _csrf: None = Depends(csrf_protect),
    ) -> dict[str, Any]:
        return await use_case.set_crypto_config(payload=body)

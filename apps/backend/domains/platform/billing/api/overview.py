from __future__ import annotations

from typing import Any

from fastapi import APIRouter, Depends, Query

from domains.platform.iam.security import csrf_protect, require_role_db

from .deps import (
    get_overview_metrics_use_case,
    get_overview_use_case,
)


def register_overview_routes(router: APIRouter) -> None:
    @router.get("/overview/dashboard")
    async def overview_dashboard(
        use_case=Depends(get_overview_use_case),
        _ops: None = Depends(require_role_db("support")),
    ) -> dict[str, Any]:
        return await use_case.dashboard()

    @router.get("/overview/networks")
    async def overview_networks(
        use_case=Depends(get_overview_use_case),
        _ops: None = Depends(require_role_db("support")),
    ) -> dict[str, Any]:
        return await use_case.networks()

    @router.get("/overview/payouts")
    async def overview_payouts(
        status: str | None = Query(None, description="Filter by transaction status"),
        limit: int = Query(50, ge=1, le=500),
        use_case=Depends(get_overview_use_case),
        _ops: None = Depends(require_role_db("support")),
    ) -> dict[str, Any]:
        return await use_case.payouts(status=status, limit=limit)

    @router.get("/overview/users/{user_id}/summary")
    async def overview_user_summary(
        user_id: str,
        metrics=Depends(get_overview_metrics_use_case),
        _ops: None = Depends(require_role_db("support")),
    ) -> dict[str, Any]:
        return await metrics.summary(user_id=user_id)

    @router.get("/overview/users/{user_id}/history")
    async def overview_user_history(
        user_id: str,
        limit: int = Query(20, ge=1, le=100),
        metrics=Depends(get_overview_metrics_use_case),
        _ops: None = Depends(require_role_db("support")),
    ) -> dict[str, Any]:
        return await metrics.history(user_id=user_id, limit=limit)

    @router.get("/overview/crypto-config")
    async def overview_get_crypto_config(
        metrics=Depends(get_overview_metrics_use_case),
        _ops: None = Depends(require_role_db("support")),
    ) -> dict[str, Any]:
        return await metrics.get_crypto_config()

    @router.post("/overview/crypto-config")
    async def overview_set_crypto_config(
        body: dict[str, Any],
        metrics=Depends(get_overview_metrics_use_case),
        _ops: None = Depends(require_role_db("support")),
        _csrf: None = Depends(csrf_protect),
    ) -> dict[str, Any]:
        return await metrics.set_crypto_config(payload=body)


__all__ = ["register_overview_routes"]

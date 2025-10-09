from __future__ import annotations

from typing import Any

from fastapi import APIRouter, Depends, HTTPException

from domains.platform.billing.application.use_cases.exceptions import (
    BillingUseCaseError,
)
from domains.platform.iam.security import csrf_protect, require_admin

from ..deps import get_admin_contracts_use_case


def register(router: APIRouter) -> None:
    @router.get("/admin/contracts")
    async def admin_list_contracts(
        use_case=Depends(get_admin_contracts_use_case),
        _admin: None = Depends(require_admin),
    ) -> dict[str, Any]:
        return await use_case.list_contracts()

    @router.post("/admin/contracts")
    async def admin_upsert_contract(
        body: dict[str, Any],
        use_case=Depends(get_admin_contracts_use_case),
        _admin: None = Depends(require_admin),
        _csrf: None = Depends(csrf_protect),
    ) -> dict[str, Any]:
        try:
            return await use_case.upsert_contract(payload=body)
        except BillingUseCaseError as exc:
            raise HTTPException(status_code=exc.status_code, detail=exc.detail) from exc

    @router.delete("/admin/contracts/{id_or_slug}")
    async def admin_delete_contract(
        id_or_slug: str,
        use_case=Depends(get_admin_contracts_use_case),
        _admin: None = Depends(require_admin),
        _csrf: None = Depends(csrf_protect),
    ) -> dict[str, Any]:
        try:
            return await use_case.delete_contract(id_or_slug=id_or_slug)
        except BillingUseCaseError as exc:
            raise HTTPException(status_code=exc.status_code, detail=exc.detail) from exc

    @router.get("/admin/contracts/{id_or_slug}/events")
    async def admin_contract_events(
        id_or_slug: str,
        limit: int = 100,
        use_case=Depends(get_admin_contracts_use_case),
        _admin: None = Depends(require_admin),
    ) -> dict[str, Any]:
        return await use_case.list_events(id_or_slug=id_or_slug, limit=limit)

    @router.post("/admin/contracts/{id_or_slug}/events")
    async def admin_add_contract_event(
        id_or_slug: str,
        body: dict[str, Any],
        use_case=Depends(get_admin_contracts_use_case),
        _admin: None = Depends(require_admin),
        _csrf: None = Depends(csrf_protect),
    ) -> dict[str, Any]:
        try:
            return await use_case.add_event(id_or_slug=id_or_slug, payload=body)
        except BillingUseCaseError as exc:
            raise HTTPException(status_code=exc.status_code, detail=exc.detail) from exc

    @router.get("/admin/contracts/events")
    async def admin_all_contract_events(
        limit: int = 100,
        use_case=Depends(get_admin_contracts_use_case),
        _admin: None = Depends(require_admin),
    ) -> dict[str, Any]:
        return await use_case.list_all_events(limit=limit)

    @router.get("/admin/contracts/metrics")
    async def admin_contract_metrics(
        id_or_slug: str | None = None,
        window: int = 1000,
        use_case=Depends(get_admin_contracts_use_case),
        _admin: None = Depends(require_admin),
    ) -> dict[str, Any]:
        return await use_case.metrics_methods(id_or_slug=id_or_slug, window=window)

    @router.get("/admin/contracts/metrics_ts")
    async def admin_contract_metrics_ts(
        id_or_slug: str | None = None,
        days: int = 30,
        use_case=Depends(get_admin_contracts_use_case),
        _admin: None = Depends(require_admin),
    ) -> dict[str, Any]:
        return await use_case.metrics_timeseries(id_or_slug=id_or_slug, days=days)

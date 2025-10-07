from __future__ import annotations

from typing import Any

from fastapi import APIRouter, Depends, HTTPException

from domains.platform.billing.application.use_cases.exceptions import (
    BillingUseCaseError,
)
from domains.platform.iam.security import csrf_protect, require_admin

from ..deps import get_admin_providers_use_case


def register(router: APIRouter) -> None:
    @router.get("/admin/providers")
    async def admin_list_providers(
        use_case=Depends(get_admin_providers_use_case),
        _admin: None = Depends(require_admin),
    ) -> dict[str, Any]:
        return await use_case.list_providers()

    @router.post("/admin/providers")
    async def admin_upsert_provider(
        body: dict[str, Any],
        use_case=Depends(get_admin_providers_use_case),
        _admin: None = Depends(require_admin),
        _csrf: None = Depends(csrf_protect),
    ) -> dict[str, Any]:
        try:
            return await use_case.upsert_provider(payload=body)
        except BillingUseCaseError as exc:
            raise HTTPException(status_code=exc.status_code, detail=exc.detail) from exc

    @router.delete("/admin/providers/{slug}")
    async def admin_delete_provider(
        slug: str,
        use_case=Depends(get_admin_providers_use_case),
        _admin: None = Depends(require_admin),
        _csrf: None = Depends(csrf_protect),
    ) -> dict[str, Any]:
        try:
            return await use_case.delete_provider(slug=slug)
        except BillingUseCaseError as exc:
            raise HTTPException(status_code=exc.status_code, detail=exc.detail) from exc

    @router.get("/admin/transactions")
    async def admin_list_transactions(
        limit: int = 100,
        use_case=Depends(get_admin_providers_use_case),
        _admin: None = Depends(require_admin),
    ) -> dict[str, Any]:
        return await use_case.list_transactions(limit=limit)

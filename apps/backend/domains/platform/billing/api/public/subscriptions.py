from __future__ import annotations

from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Query

from domains.platform.billing.application.use_cases.exceptions import (
    BillingUseCaseError,
)
from domains.platform.iam.security import get_current_user

from ..deps import get_public_use_cases


def register(router: APIRouter) -> None:
    @router.get("/subscriptions/me")
    async def my_subscription(
        claims=Depends(get_current_user),
        use_cases=Depends(get_public_use_cases),
    ) -> dict[str, Any]:
        user_id = str(claims.get("sub")) if claims and claims.get("sub") else None
        try:
            return await use_cases.get_my_subscription(user_id=user_id)
        except BillingUseCaseError as exc:
            raise HTTPException(status_code=exc.status_code, detail=exc.detail) from exc

    @router.get("/me/summary")
    async def my_billing_summary(
        claims=Depends(get_current_user),
        use_cases=Depends(get_public_use_cases),
    ) -> dict[str, Any]:
        user_id = str(claims.get("sub")) if claims and claims.get("sub") else None
        try:
            return await use_cases.get_my_summary(user_id=user_id)
        except BillingUseCaseError as exc:
            raise HTTPException(status_code=exc.status_code, detail=exc.detail) from exc

    @router.get("/me/history")
    async def my_billing_history(
        claims=Depends(get_current_user),
        limit: int = Query(20, ge=1, le=100),
        use_cases=Depends(get_public_use_cases),
    ) -> dict[str, Any]:
        user_id = str(claims.get("sub")) if claims and claims.get("sub") else None
        try:
            return await use_cases.get_my_history(user_id=user_id, limit=limit)
        except BillingUseCaseError as exc:
            raise HTTPException(status_code=exc.status_code, detail=exc.detail) from exc

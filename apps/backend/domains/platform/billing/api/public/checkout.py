from __future__ import annotations

from typing import Any

from fastapi import APIRouter, Depends, HTTPException

from domains.platform.billing.application.use_cases.exceptions import (
    BillingUseCaseError,
)
from domains.platform.iam.security import csrf_protect, get_current_user

from ..deps import CHECKOUT_RATE_LIMITER, get_public_use_cases


def register(router: APIRouter) -> None:
    @router.post("/checkout", dependencies=CHECKOUT_RATE_LIMITER)
    async def checkout(
        body: dict[str, Any],
        claims=Depends(get_current_user),
        use_cases=Depends(get_public_use_cases),
        _csrf: None = Depends(csrf_protect),
    ) -> dict[str, Any]:
        user_id = str(claims.get("sub")) if claims and claims.get("sub") else None
        plan_slug = body.get("plan")
        try:
            return await use_cases.checkout(user_id=user_id, plan_slug=plan_slug)
        except BillingUseCaseError as exc:
            raise HTTPException(status_code=exc.status_code, detail=exc.detail) from exc

from __future__ import annotations

from typing import Any

from fastapi import APIRouter, Depends, Response, status

from apps.backend.domains.platform.billing.api.deps import get_settings_use_case
from apps.backend.domains.platform.billing.application.use_cases import (
    BillingSettingsUseCase,
)
from domains.platform.iam.security import get_current_user, require_admin
from packages.core.errors import ApiError

from .common import require_user_id, settings_payload


def register(admin_router: APIRouter, personal_router: APIRouter) -> None:
    @admin_router.get("/billing/{user_id}")
    async def settings_billing_get(
        user_id: str,
        response: Response,
        _admin: None = Depends(require_admin),
        use_case: BillingSettingsUseCase = Depends(get_settings_use_case),
    ) -> dict[str, Any]:
        try:
            data = await use_case.build_bundle(user_id)
        except RuntimeError:
            raise ApiError(
                code="E_BILLING_UNAVAILABLE",
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                message="Billing backend unavailable",
            ) from None
        return settings_payload(response, "billing", data)

    @personal_router.get("/billing")
    async def me_settings_billing_get(
        response: Response,
        claims=Depends(get_current_user),
        use_case: BillingSettingsUseCase = Depends(get_settings_use_case),
    ) -> dict[str, Any]:
        user_id = require_user_id(claims)
        try:
            data = await use_case.build_bundle(user_id)
        except RuntimeError:
            raise ApiError(
                code="E_BILLING_UNAVAILABLE",
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                message="Billing backend unavailable",
            ) from None
        return settings_payload(response, "billing", data)


__all__ = ["register"]

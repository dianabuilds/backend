from __future__ import annotations

import logging
from typing import Any

from fastapi import APIRouter, Depends, Request, Response, status

from domains.platform.iam.security import get_current_user, require_admin
from domains.product.profile.application.profile_presenter import profile_to_dict
from packages.core.errors import ApiError

from ..routers import get_container
from .common import require_user_id, settings_payload

logger = logging.getLogger(__name__)


async def _billing_bundle(container, user_id: str) -> dict[str, Any]:
    svc = container.billing.service
    summary = await svc.get_summary_for_user(user_id)
    history = await svc.get_history_for_user(user_id)
    wallet = None
    try:
        profile_view = await container.profile_service.get_profile(user_id)
        wallet = profile_to_dict(profile_view).get("wallet")
    except ValueError:
        wallet = None
    except Exception as exc:
        logger.exception(
            "Failed to fetch profile while building billing bundle", exc_info=exc
        )
        wallet = None
    return {"summary": summary, "history": history, "wallet": wallet}


def register(admin_router: APIRouter, personal_router: APIRouter) -> None:
    @admin_router.get("/billing/{user_id}")
    async def settings_billing_get(
        user_id: str,
        request: Request,
        response: Response,
        _admin: None = Depends(require_admin),
    ) -> dict[str, Any]:
        container = get_container(request)
        try:
            data = await _billing_bundle(container, user_id)
        except RuntimeError:
            raise ApiError(
                code="E_BILLING_UNAVAILABLE",
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                message="Billing backend unavailable",
            ) from None
        return settings_payload(response, "billing", data)

    @personal_router.get("/billing")
    async def me_settings_billing_get(
        request: Request,
        response: Response,
        claims=Depends(get_current_user),
    ) -> dict[str, Any]:
        user_id = require_user_id(claims)
        container = get_container(request)
        try:
            data = await _billing_bundle(container, user_id)
        except RuntimeError:
            raise ApiError(
                code="E_BILLING_UNAVAILABLE",
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                message="Billing backend unavailable",
            ) from None
        return settings_payload(response, "billing", data)


__all__ = ["register"]

from __future__ import annotations

import logging
from functools import lru_cache
from typing import Any

from fastapi import APIRouter, Depends, Header, Request, Response, status
from pydantic import BaseModel

from domains.platform.iam.security import csrf_protect, get_current_user, require_admin
from domains.platform.notifications.adapters.sql.matrix import SQLNotificationMatrixRepo
from domains.platform.notifications.adapters.sql.preferences import (
    SQLNotificationPreferenceRepo,
)
from domains.platform.notifications.application.preference_service import (
    PreferenceService,
)
from packages.core.errors import ApiError
from packages.core.settings_contract import assert_if_match, compute_etag

from ..idempotency import IDEMPOTENCY_HEADER, require_idempotency_key
from ..routers import get_container
from .common import dsn_from_settings, engine_for_dsn, require_user_id, settings_payload

logger = logging.getLogger(__name__)


class NotificationPreferencesPayload(BaseModel):
    preferences: dict[str, Any]


@lru_cache(maxsize=4)
def _preference_service_for_dsn(dsn: str) -> PreferenceService:
    engine = engine_for_dsn(dsn)
    preference_repo = SQLNotificationPreferenceRepo(engine)
    matrix_repo = SQLNotificationMatrixRepo(engine)
    return PreferenceService(matrix_repo=matrix_repo, preference_repo=preference_repo)


def _get_preference_service(container) -> PreferenceService:
    svc = getattr(
        getattr(container, "notifications", object()), "preference_service", None
    )
    if svc is not None:
        return svc
    dsn = dsn_from_settings(container.settings)
    return _preference_service_for_dsn(dsn)


def register(admin_router: APIRouter, personal_router: APIRouter) -> None:
    @admin_router.get("/notifications/{user_id}/preferences")
    async def settings_notifications_get(
        user_id: str,
        request: Request,
        response: Response,
        _admin: None = Depends(require_admin),
    ) -> dict[str, Any]:
        container = get_container(request)
        try:
            prefs = await _get_preference_service(container).get_preferences(user_id)
        except RuntimeError:
            raise ApiError(
                code="E_NOTIFICATIONS_UNAVAILABLE",
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                message="Notifications backend unavailable",
            ) from None
        return settings_payload(response, "preferences", prefs)

    @admin_router.put(
        "/notifications/{user_id}/preferences",
        dependencies=[Depends(require_idempotency_key), Depends(csrf_protect)],
    )
    async def settings_notifications_put(
        user_id: str,
        body: NotificationPreferencesPayload,
        request: Request,
        response: Response,
        if_match: str | None = Header(default=None, alias="If-Match"),
        _admin: None = Depends(require_admin),
    ) -> dict[str, Any]:
        container = get_container(request)
        svc = _get_preference_service(container)
        try:
            current = await svc.get_preferences(user_id)
        except RuntimeError:
            raise ApiError(
                code="E_NOTIFICATIONS_UNAVAILABLE",
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                message="Notifications backend unavailable",
            ) from None
        assert_if_match(if_match, compute_etag(current))
        await svc.set_preferences(user_id, body.preferences)
        updated = await svc.get_preferences(user_id)
        payload = settings_payload(response, "preferences", updated)
        try:
            await container.audit.service.log(
                actor_id=None,
                action="notifications.preferences.updated",
                resource_type="user",
                resource_id=user_id,
                after=updated,
            )
        except Exception as exc:
            logger.exception(
                "Failed to audit admin notification preference update", exc_info=exc
            )
        return payload

    @personal_router.get("/notifications/preferences")
    async def me_settings_notifications_get(
        request: Request,
        response: Response,
        claims=Depends(get_current_user),
    ) -> dict[str, Any]:
        user_id = require_user_id(claims)
        container = get_container(request)
        svc = _get_preference_service(container)
        context = claims or {"sub": user_id}
        try:
            overview = await svc.get_preferences_overview(user_id, context=context)
        except RuntimeError:
            raise ApiError(
                code="E_NOTIFICATIONS_UNAVAILABLE",
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                message="Notifications backend unavailable",
            ) from None
        return settings_payload(response, "overview", overview)

    @personal_router.put(
        "/notifications/preferences",
        dependencies=[Depends(require_idempotency_key), Depends(csrf_protect)],
    )
    async def me_settings_notifications_put(
        body: NotificationPreferencesPayload,
        request: Request,
        response: Response,
        if_match: str | None = Header(default=None, alias="If-Match"),
        claims=Depends(get_current_user),
    ) -> dict[str, Any]:
        user_id = require_user_id(claims)
        container = get_container(request)
        svc = _get_preference_service(container)
        context = claims or {"sub": user_id}
        try:
            current = await svc.get_preferences_overview(user_id, context=context)
        except RuntimeError:
            raise ApiError(
                code="E_NOTIFICATIONS_UNAVAILABLE",
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                message="Notifications backend unavailable",
            ) from None
        assert_if_match(if_match, compute_etag(current))
        request_id = request.headers.get(IDEMPOTENCY_HEADER)
        await svc.set_preferences(
            user_id,
            body.preferences,
            actor_id=user_id,
            source="user",
            context=context,
            request_id=request_id,
        )
        updated = await svc.get_preferences_overview(user_id, context=context)
        payload = settings_payload(response, "overview", updated)
        try:
            await container.audit.service.log(
                actor_id=user_id,
                action="notifications.preferences.updated",
                resource_type="user",
                resource_id=user_id,
                after=updated,
            )
        except Exception as exc:
            logger.exception(
                "Failed to audit user notification preference update", exc_info=exc
            )
        return payload


__all__ = ["NotificationPreferencesPayload", "register"]

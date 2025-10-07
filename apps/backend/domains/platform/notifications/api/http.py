from __future__ import annotations

import logging
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Query, Request
from pydantic import BaseModel, Field

from apps.backend.app.api_gateway.routers import get_container
from domains.platform.iam.security import csrf_protect, get_current_user, require_admin
from domains.platform.notifications.application.dispatch_use_cases import (
    preview_channel_notification as preview_channel_notification_use_case,
)
from domains.platform.notifications.application.dispatch_use_cases import (
    send_channel_notification as send_channel_notification_use_case,
)
from domains.platform.notifications.application.messages_exceptions import (
    NotificationError,
)
from domains.platform.notifications.application.messages_use_cases import (
    list_notifications as list_notifications_use_case,
)
from domains.platform.notifications.application.messages_use_cases import (
    mark_notification_read as mark_notification_read_use_case,
)
from domains.platform.notifications.application.preferences_use_cases import (
    get_preferences as get_preferences_use_case,
)
from domains.platform.notifications.application.preferences_use_cases import (
    set_preferences as set_preferences_use_case,
)
from domains.platform.notifications.logic.dispatcher import dispatch
from packages.core import validate_notifications_request
from packages.fastapi_rate_limit import optional_rate_limiter

try:
    from jsonschema.exceptions import ValidationError as JsonSchemaValidationError  # type: ignore
except ImportError:  # pragma: no cover

    class JsonSchemaValidationError(ValueError):  # type: ignore[no-redef]
        """Fallback validation error when jsonschema is unavailable."""

        pass


logger = logging.getLogger(__name__)


class PreferenceBody(BaseModel):
    preferences: dict[str, Any]


class TestNotificationBody(BaseModel):
    channel: str = Field(min_length=1)
    payload: dict[str, Any] | None = None


class SendIn(BaseModel):
    channel: str = Field(min_length=1, examples=["log", "webhook"])
    payload: dict[str, Any]


def _raise_notification_error(error: NotificationError) -> None:
    headers = error.headers or None
    raise HTTPException(
        status_code=error.status_code, detail=error.code, headers=headers
    ) from error


def make_router() -> APIRouter:
    router = APIRouter(prefix="/v1/notifications")

    @router.get("/preferences")
    async def get_preferences(
        req: Request,
        claims=Depends(get_current_user),
    ) -> dict[str, Any]:
        container = get_container(req)
        try:
            result = await get_preferences_use_case(
                container.notifications.preference_service,
                container.users.service,
                subject=str(claims.get("sub") or ""),
                context={"sub": claims.get("sub")},
            )
        except NotificationError as error:
            _raise_notification_error(error)
        return result

    @router.put("/preferences", dependencies=[Depends(csrf_protect)])
    async def set_preferences(
        req: Request,
        body: PreferenceBody,
        claims=Depends(get_current_user),
    ) -> dict[str, Any]:
        container = get_container(req)
        try:
            result = await set_preferences_use_case(
                container.notifications.preference_service,
                container.users.service,
                subject=str(claims.get("sub") or ""),
                preferences=body.preferences,
            )
        except NotificationError as error:
            _raise_notification_error(error)
        return result

    @router.get(
        "",
        dependencies=(optional_rate_limiter(times=60, seconds=60)),
    )
    async def list_my_notifications(
        req: Request,
        limit: int = Query(default=50, ge=1, le=200),
        offset: int = Query(default=0, ge=0),
        claims=Depends(get_current_user),
    ) -> dict[str, Any]:
        container = get_container(req)
        try:
            result = await list_notifications_use_case(
                container.notifications.repo,
                container.users.service,
                subject=str(claims.get("sub") or ""),
                placement="inbox",
                limit=limit,
                offset=offset,
            )
        except NotificationError as error:
            _raise_notification_error(error)
        return result

    @router.post(
        "/read/{notif_id}",
        dependencies=(optional_rate_limiter(times=60, seconds=60)),
    )
    async def mark_read(
        req: Request,
        notif_id: str,
        claims=Depends(get_current_user),
        _csrf: None = Depends(csrf_protect),
    ) -> dict[str, Any]:
        container = get_container(req)
        try:
            result = await mark_notification_read_use_case(
                container.notifications.repo,
                container.users.service,
                subject=str(claims.get("sub") or ""),
                notification_id=notif_id,
            )
        except NotificationError as error:
            _raise_notification_error(error)
        return result

    @router.post(
        "/test",
        dependencies=[Depends(csrf_protect)],
    )
    async def test_notification(
        body: TestNotificationBody,
        _claims=Depends(get_current_user),
    ) -> dict[str, Any]:
        try:
            result = preview_channel_notification_use_case(
                dispatch,
                channel=body.channel,
                payload=body.payload,
                logger=logger,
            )
        except NotificationError as error:
            _raise_notification_error(error)
        return result

    @router.post(
        "/send",
        dependencies=[Depends(require_admin), Depends(csrf_protect)],
    )
    async def send_notification(
        body: SendIn,
    ) -> dict[str, Any]:
        try:
            result = send_channel_notification_use_case(
                dispatch,
                validate_notifications_request,
                channel=body.channel,
                payload=body.payload,
                logger=logger,
                validation_errors=(
                    JsonSchemaValidationError,
                    ValueError,
                    TypeError,
                ),
            )
        except NotificationError as error:
            _raise_notification_error(error)
        return result

    return router


__all__ = ["make_router"]

from __future__ import annotations

from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Query, Request

from apps.backend.app.api_gateway.routers import get_container
from domains.platform.iam.security import (
    csrf_protect,
    get_current_user,
    require_admin,
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
from domains.platform.notifications.application.messages_use_cases import (
    send_notification as send_notification_use_case,
)
from packages.fastapi_rate_limit import optional_rate_limiter


def _raise_notification_error(error: NotificationError) -> None:
    headers = error.headers or None
    raise HTTPException(
        status_code=error.status_code, detail=error.code, headers=headers
    ) from error


def make_router() -> APIRouter:
    router = APIRouter(prefix="/v1/notifications", tags=["notifications"])

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
        "/admin/send",
        dependencies=(optional_rate_limiter(times=10, seconds=60)),
    )
    async def admin_send(
        req: Request,
        body: dict[str, Any],
        _admin: None = Depends(require_admin),
        _csrf: None = Depends(csrf_protect),
    ) -> dict[str, Any]:
        container = get_container(req)
        try:
            result = await send_notification_use_case(
                container.notifications.notify,
                body,
            )
        except NotificationError as error:
            _raise_notification_error(error)
        return result

    return router


__all__ = ["make_router"]

from __future__ import annotations

import json
import uuid
from collections.abc import Mapping
from typing import Any

from domains.platform.notifications.application.messages_exceptions import (
    NotificationError,
)
from domains.platform.notifications.application.messages_presenter import (
    NotificationResponse,
    NotificationsListResponse,
    build_list_response,
    build_single_response,
    notification_to_dict,
)


async def resolve_user_id(users_service: Any, subject: str | None) -> str:
    identifier = str(subject or "").strip()
    if not identifier:
        raise NotificationError(code="unauthenticated", status_code=401)
    user = await users_service.get(identifier)
    if user and getattr(user, "id", None):
        return str(user.id)
    try:
        uuid.UUID(identifier)
        return identifier
    except ValueError:
        return str(uuid.uuid5(uuid.NAMESPACE_DNS, f"user:{identifier}"))


async def list_notifications(
    repo: Any,
    users_service: Any,
    *,
    subject: str | None,
    placement: str = "inbox",
    limit: int = 50,
    offset: int = 0,
) -> NotificationsListResponse:
    user_id = await resolve_user_id(users_service, subject)
    rows = await repo.list_for_user(
        user_id,
        placement=placement,
        limit=limit,
        offset=offset,
    )
    items = [notification_to_dict(row) for row in rows]
    return build_list_response(items)


async def mark_notification_read(
    repo: Any,
    users_service: Any,
    *,
    subject: str | None,
    notification_id: str,
) -> NotificationResponse:
    user_id = await resolve_user_id(users_service, subject)
    updated = await repo.mark_read(user_id, notification_id)
    if not updated:
        raise NotificationError(code="not_found", status_code=404)
    return build_single_response(updated)


def _normalize_meta(raw: Any) -> Mapping[str, Any] | None:
    if isinstance(raw, Mapping):
        return dict(raw)
    if isinstance(raw, str):
        stripped = raw.strip()
        if not stripped:
            return None
        try:
            parsed = json.loads(stripped)
        except json.JSONDecodeError:
            return None
        if isinstance(parsed, Mapping):
            return dict(parsed)
        return None
    return None


async def send_notification(
    notify_service: Any,
    payload: Any,
) -> NotificationResponse:
    if not isinstance(payload, Mapping):
        raise NotificationError(
            code="invalid_payload",
            status_code=400,
            message="payload must be an object",
        )
    user_id = str(payload.get("user_id") or "").strip()
    if not user_id:
        raise NotificationError(code="user_id_required", status_code=400)
    title = str(payload.get("title") or "")
    message = str(payload.get("message") or "")
    type_ = str(payload.get("type") or "system")
    placement = str(payload.get("placement") or "inbox")
    topic_key = payload.get("topic_key")
    channel_key = payload.get("channel_key")
    priority = str(payload.get("priority") or "normal")
    cta_label = payload.get("cta_label")
    cta_url = payload.get("cta_url")
    meta = _normalize_meta(payload.get("meta"))
    event_id = payload.get("event_id")

    dto = await notify_service.create_notification(
        user_id=user_id,
        title=title,
        message=message,
        type_=type_,
        placement=placement,
        topic_key=topic_key,
        channel_key=channel_key,
        priority=priority,
        cta_label=cta_label,
        cta_url=cta_url,
        meta=meta,
        event_id=event_id,
    )
    return build_single_response(dto)


__all__ = [
    "list_notifications",
    "mark_notification_read",
    "send_notification",
]

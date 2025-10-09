from __future__ import annotations

import json
from collections.abc import Mapping
from datetime import datetime
from typing import Any, TypedDict, cast


class NotificationPayload(TypedDict, total=False):
    id: str
    user_id: str
    channel: str | None
    title: str | None
    message: str | None
    type: str | None
    priority: str
    meta: dict[str, Any]
    created_at: str | None
    updated_at: str | None
    read_at: str | None
    is_read: bool


class NotificationsListResponse(TypedDict):
    items: list[NotificationPayload]
    unread: int


class NotificationResponse(TypedDict):
    notification: NotificationPayload


def _iso(value: datetime | None) -> str | None:
    return value.isoformat() if isinstance(value, datetime) else None


def notification_to_dict(row: Mapping[str, Any]) -> NotificationPayload:
    data = dict(row)
    for field in ("created_at", "updated_at", "read_at"):
        data[field] = _iso(data.get(field))
    meta = data.get("meta")
    if isinstance(meta, Mapping):
        normalized_meta = dict(meta)
    elif isinstance(meta, str):
        try:
            normalized_meta = json.loads(meta)
        except json.JSONDecodeError:
            normalized_meta = {}
    else:
        normalized_meta = {}
    data["meta"] = normalized_meta
    data["priority"] = str(data.get("priority") or "normal")
    data["is_read"] = data.get("read_at") is not None
    return cast(NotificationPayload, data)


def build_list_response(items: list[NotificationPayload]) -> NotificationsListResponse:
    unread = sum(1 for item in items if not item.get("is_read"))
    return NotificationsListResponse(items=list(items), unread=unread)


def build_single_response(notification: Mapping[str, Any]) -> NotificationResponse:
    payload = notification_to_dict(notification)
    return NotificationResponse(notification=payload)


__all__ = [
    "NotificationPayload",
    "NotificationResponse",
    "NotificationsListResponse",
    "build_list_response",
    "build_single_response",
    "notification_to_dict",
]

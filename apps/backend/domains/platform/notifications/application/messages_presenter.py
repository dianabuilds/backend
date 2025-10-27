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


class NotificationsListResponse(TypedDict, total=False):
    items: list[NotificationPayload]
    unread: int
    unread_total: int
    total: int
    has_more: bool
    limit: int
    offset: int


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


def build_list_response(
    items: list[NotificationPayload],
    *,
    total: int,
    unread_total: int,
    limit: int,
    offset: int,
) -> NotificationsListResponse:
    effective_limit = max(int(limit), 0)
    effective_offset = max(int(offset), 0)
    effective_unread = max(int(unread_total), 0)
    effective_total = max(int(total), 0)
    page_count = len(items)
    has_more = effective_offset + page_count < effective_total
    return NotificationsListResponse(
        items=list(items),
        unread=effective_unread,
        unread_total=effective_unread,
        total=effective_total,
        has_more=has_more,
        limit=effective_limit,
        offset=effective_offset,
    )


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

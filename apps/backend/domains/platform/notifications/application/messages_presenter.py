from __future__ import annotations

import json
from collections.abc import Mapping
from datetime import datetime
from typing import Any


def _iso(value: datetime | None) -> str | None:
    return value.isoformat() if isinstance(value, datetime) else None


def notification_to_dict(row: Mapping[str, Any]) -> dict[str, Any]:
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
    return data


def build_list_response(items: list[dict[str, Any]]) -> dict[str, Any]:
    unread = sum(1 for item in items if not item.get("is_read"))
    return {"items": items, "unread": unread}


def build_single_response(notification: Mapping[str, Any]) -> dict[str, Any]:
    return {"notification": notification_to_dict(notification)}


__all__ = [
    "build_list_response",
    "build_single_response",
    "notification_to_dict",
]

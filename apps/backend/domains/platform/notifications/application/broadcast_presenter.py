from __future__ import annotations

from collections.abc import Mapping
from datetime import datetime
from typing import Any

from domains.platform.notifications.domain.broadcast import (
    Broadcast,
    BroadcastAudience,
    BroadcastCollection,
    BroadcastStatus,
)


def _iso(value: datetime | None) -> str | None:
    return value.isoformat() if value else None


def audience_to_dict(audience: BroadcastAudience) -> dict[str, Any]:
    filters: Mapping[str, Any] | None = audience.filters
    user_ids = list(audience.user_ids) if audience.user_ids else None
    return {
        "type": audience.type.value,
        "filters": dict(filters) if filters is not None else None,
        "user_ids": user_ids,
    }


def broadcast_to_dict(broadcast: Broadcast) -> dict[str, Any]:
    return {
        "id": broadcast.id,
        "title": broadcast.title,
        "body": broadcast.body,
        "template_id": broadcast.template_id,
        "audience": audience_to_dict(broadcast.audience),
        "status": broadcast.status.value,
        "created_by": broadcast.created_by,
        "created_at": _iso(broadcast.created_at),
        "updated_at": _iso(broadcast.updated_at),
        "scheduled_at": _iso(broadcast.scheduled_at),
        "started_at": _iso(broadcast.started_at),
        "finished_at": _iso(broadcast.finished_at),
        "total": broadcast.total,
        "sent": broadcast.sent,
        "failed": broadcast.failed,
    }


def build_broadcast_list_response(
    collection: BroadcastCollection, *, limit: int, offset: int
) -> dict[str, Any]:
    items = [broadcast_to_dict(item) for item in collection.items]
    has_next = offset + len(items) < collection.total
    counts: dict[str, int] = {}
    for status in BroadcastStatus:
        counts[status.value] = int(
            collection.status_counts.get(
                status, collection.status_counts.get(status.value, 0)
            )
        )
    return {
        "items": items,
        "total": collection.total,
        "offset": offset,
        "limit": limit,
        "has_next": has_next,
        "status_counts": counts,
        "recipients": collection.recipient_total,
    }


__all__ = [
    "audience_to_dict",
    "broadcast_to_dict",
    "build_broadcast_list_response",
]

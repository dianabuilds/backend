from __future__ import annotations

from datetime import UTC, datetime

from domains.platform.notifications.application.broadcast_presenter import (
    broadcast_to_dict,
    build_broadcast_list_response,
)
from domains.platform.notifications.domain.broadcast import (
    Broadcast,
    BroadcastAudience,
    BroadcastAudienceType,
    BroadcastCollection,
    BroadcastStatus,
)


def _sample_broadcast() -> Broadcast:
    now = datetime(2025, 1, 1, 12, 0, tzinfo=UTC)
    audience = BroadcastAudience(type=BroadcastAudienceType.ALL_USERS)
    return Broadcast(
        id="b-1",
        title="Launch",
        body="Hello",
        template_id=None,
        audience=audience,
        status=BroadcastStatus.DRAFT,
        created_by="system",
        created_at=now,
        updated_at=now,
        scheduled_at=now,
        started_at=None,
        finished_at=None,
        total=10,
        sent=0,
        failed=0,
    )


def test_broadcast_to_dict_serializes_iso_and_status() -> None:
    broadcast = _sample_broadcast()
    payload = broadcast_to_dict(broadcast)

    assert payload["id"] == "b-1"
    assert payload["status"] == BroadcastStatus.DRAFT.value
    assert payload["created_at"] == "2025-01-01T12:00:00+00:00"
    assert payload["audience"]["type"] == BroadcastAudienceType.ALL_USERS.value
    assert payload["audience"]["user_ids"] is None


def test_build_broadcast_list_response_includes_all_status_counts() -> None:
    broadcast = _sample_broadcast()
    collection = BroadcastCollection(
        items=(broadcast,),
        total=5,
        status_counts={BroadcastStatus.DRAFT: 2, BroadcastStatus.SENT: 1},
        recipient_total=42,
    )

    payload = build_broadcast_list_response(collection, limit=2, offset=0)

    assert payload["has_next"] is True
    assert payload["total"] == 5
    assert payload["recipients"] == 42
    assert payload["status_counts"][BroadcastStatus.DRAFT.value] == 2
    assert payload["status_counts"][BroadcastStatus.SCHEDULED.value] == 0
    assert payload["items"][0]["audience"]["filters"] is None

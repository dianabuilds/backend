from __future__ import annotations


from datetime import UTC, datetime

from typing import Any, Sequence


import pytest


from domains.platform.notifications.application.broadcast_exceptions import (
    BroadcastError,
)

from domains.platform.notifications.application.broadcast_service import (
    BroadcastNotFoundError,
    BroadcastStatusError,
    BroadcastValidationError,
)

from domains.platform.notifications.application.broadcast_use_cases import (
    cancel_broadcast,
    create_broadcast,
    list_broadcasts,
    schedule_broadcast,
    send_broadcast_now,
    update_broadcast,
)

from domains.platform.notifications.domain.broadcast import (
    Broadcast,
    BroadcastAudience,
    BroadcastAudienceType,
    BroadcastCollection,
    BroadcastStatus,
)


def _broadcast() -> Broadcast:

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
        total=100,
        sent=0,
        failed=0,
    )


def _collection(broadcasts: Sequence[Broadcast]) -> BroadcastCollection:

    return BroadcastCollection(
        items=tuple(broadcasts),
        total=len(broadcasts),
        status_counts={BroadcastStatus.DRAFT: len(broadcasts)},
        recipient_total=10,
    )


class ListStubService:

    def __init__(self, result: BroadcastCollection) -> None:

        self.result = result

        self.received: dict[str, Any] | None = None

    async def list(
        self,
        *,
        limit: int,
        offset: int,
        statuses: Sequence[BroadcastStatus] | None,
        query: str | None,
    ) -> BroadcastCollection:

        self.received = {
            "limit": limit,
            "offset": offset,
            "statuses": statuses,
            "query": query,
        }

        return self.result


@pytest.mark.asyncio
async def test_list_broadcasts_returns_payload_and_normalizes_statuses() -> None:

    service = ListStubService(_collection([_broadcast()]))

    result = await list_broadcasts(
        service,
        limit=5,
        offset=0,
        statuses=["draft"],
        query="launch",
    )

    assert result["items"][0]["id"] == "b-1"

    assert service.received is not None

    assert service.received["statuses"] == (BroadcastStatus.DRAFT,)

    assert service.received["query"] == "launch"


@pytest.mark.asyncio
async def test_list_broadcasts_invalid_status_filter_raises_error() -> None:

    service = ListStubService(_collection([]))

    with pytest.raises(BroadcastError) as exc:

        await list_broadcasts(
            service, limit=5, offset=0, statuses=["unknown"], query=None
        )

    assert exc.value.code == "invalid_status_filter"


class CreateStubService:

    def __init__(
        self, result: Broadcast | None = None, error: Exception | None = None
    ) -> None:

        self.result = result or _broadcast()

        self.error = error

        self.received: Any = None

    async def create(self, data) -> Broadcast:

        self.received = data

        if self.error:

            raise self.error

        return self.result


@pytest.mark.asyncio
async def test_create_broadcast_passes_payload_and_returns_dict() -> None:

    service = CreateStubService()

    payload = {
        "title": "Launch",
        "body": "Hello",
        "template_id": None,
        "audience": {"type": "all_users"},
        "created_by": "admin",
    }

    result = await create_broadcast(service, payload)

    assert result["title"] == "Launch"

    assert service.received.title == "Launch"

    assert service.received.audience.type is BroadcastAudienceType.ALL_USERS


@pytest.mark.asyncio
async def test_create_broadcast_maps_validation_error() -> None:

    service = CreateStubService(error=BroadcastValidationError("missing content"))

    payload = {
        "title": "Launch",
        "body": "",
        "template_id": None,
        "audience": {"type": "all_users"},
        "created_by": "admin",
    }

    with pytest.raises(BroadcastError) as exc:

        await create_broadcast(service, payload)

    assert exc.value.code == "invalid_broadcast"

    assert "missing" in exc.value.message


class UpdateStubService:

    def __init__(self, error: Exception | None = None) -> None:

        self.error = error

        self.received: Any = None

        self.broadcast = _broadcast()

    async def update(self, broadcast_id: str, data) -> Broadcast:

        self.received = (broadcast_id, data)

        if self.error:

            raise self.error

        return self.broadcast


@pytest.mark.asyncio
async def test_update_broadcast_handles_not_found() -> None:

    service = UpdateStubService(error=BroadcastNotFoundError())

    payload = {
        "title": "Launch",
        "body": "Hello",
        "template_id": None,
        "audience": {"type": "all_users"},
        "scheduled_at": datetime(2025, 1, 1, 13, 0, tzinfo=UTC),
    }

    with pytest.raises(BroadcastError) as exc:

        await update_broadcast(service, "missing", payload)

    assert exc.value.code == "broadcast_not_found"


class StatusStubService:

    def __init__(self, error: Exception | None = None) -> None:

        self.error = error

        self.broadcast = _broadcast()

        self.received: Any = None

    async def send_now(self, broadcast_id: str) -> Broadcast:

        self.received = ("send_now", broadcast_id)

        if self.error:

            raise self.error

        return self.broadcast

    async def schedule(self, broadcast_id: str, scheduled_at: datetime) -> Broadcast:

        self.received = ("schedule", broadcast_id, scheduled_at)

        if self.error:

            raise self.error

        return self.broadcast

    async def cancel(self, broadcast_id: str) -> Broadcast:

        self.received = ("cancel", broadcast_id)

        if self.error:

            raise self.error

        return self.broadcast


@pytest.mark.asyncio
async def test_schedule_broadcast_returns_payload() -> None:

    service = StatusStubService()

    scheduled_at = datetime(2025, 1, 2, 15, 0, tzinfo=UTC)

    result = await schedule_broadcast(service, "b-1", scheduled_at)

    assert result["id"] == "b-1"

    assert service.received == ("schedule", "b-1", scheduled_at)


@pytest.mark.asyncio
async def test_send_now_broadcast_maps_status_error() -> None:

    service = StatusStubService(error=BroadcastStatusError("cannot send"))

    with pytest.raises(BroadcastError) as exc:

        await send_broadcast_now(service, "b-1")

    assert exc.value.code == "invalid_status"

    assert "cannot send" in exc.value.message


@pytest.mark.asyncio
async def test_cancel_broadcast_returns_payload() -> None:

    service = StatusStubService()

    result = await cancel_broadcast(service, "b-1")

    assert result["id"] == "b-1"

    assert service.received == ("cancel", "b-1")

from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from typing import TYPE_CHECKING, Any, cast

import pytest

from domains.platform.notifications.application.audience_resolver import (
    AudienceResolutionError,
)
from domains.platform.notifications.application.broadcast_orchestrator import (
    BroadcastDeliverySummary,
    BroadcastOrchestrator,
)
from domains.platform.notifications.domain.broadcast import (
    Broadcast,
    BroadcastAudience,
    BroadcastAudienceType,
    BroadcastCollection,
    BroadcastStatus,
)
from domains.platform.notifications.ports import BroadcastRepo

if TYPE_CHECKING:
    from domains.platform.notifications.application.audience_resolver import (
        BroadcastAudienceResolver,
    )
    from domains.platform.notifications.application.delivery import (
        DeliveryService,
    )
    from domains.platform.notifications.application.template_service import (
        TemplateService,
    )


@dataclass
class _TemplateStub:
    slug: str
    locale: str | None = None


class _StubTemplateService:
    def __init__(self, mapping: dict[str, _TemplateStub]) -> None:
        self._mapping = mapping

    async def get(self, template_id: str) -> _TemplateStub | None:
        return self._mapping.get(template_id)


class _StubDelivery:
    def __init__(self, fail_ids: set[str] | None = None) -> None:
        self.events: list[Any] = []
        self._fail_ids = set(fail_ids or set())

    async def deliver_to_inbox(self, event) -> dict[str, Any] | None:
        if event.user_id in self._fail_ids:
            raise RuntimeError("delivery_failed")
        self.events.append(event)
        return {"id": event.event_id}


class _StubAudienceResolver:
    def __init__(self, mapping: dict[BroadcastAudienceType, list[str]]) -> None:
        self._mapping = mapping

    async def iter_user_ids(
        self, audience: BroadcastAudience, *, batch_size: int | None = None
    ):
        users = list(self._mapping.get(audience.type, audience.user_ids or []))
        if not users:
            return
        size = batch_size or len(users)
        for idx in range(0, len(users), size):
            yield users[idx : idx + size]


class _FailingAudienceResolver:
    async def iter_user_ids(
        self, audience: BroadcastAudience, *, batch_size: int | None = None
    ):
        raise AudienceResolutionError("boom")


class _MemoryBroadcastRepo(BroadcastRepo):
    def __init__(self) -> None:
        self._items: dict[str, Broadcast] = {}

    def add(self, broadcast: Broadcast) -> None:
        self._items[broadcast.id] = broadcast

    async def create(self, payload) -> Broadcast:
        raise NotImplementedError

    async def update(self, broadcast_id: str, payload) -> Broadcast:
        raise NotImplementedError

    async def update_status(
        self,
        broadcast_id: str,
        *,
        status: BroadcastStatus,
        scheduled_at: datetime | None = None,
        started_at: datetime | None = None,
        finished_at: datetime | None = None,
        total: int | None = None,
        sent: int | None = None,
        failed: int | None = None,
    ) -> Broadcast:
        current = self._items[broadcast_id]
        updated = Broadcast(
            id=current.id,
            title=current.title,
            body=current.body,
            template_id=current.template_id,
            audience=current.audience,
            status=status,
            created_by=current.created_by,
            created_at=current.created_at,
            updated_at=datetime.now(UTC),
            scheduled_at=current.scheduled_at if scheduled_at is None else scheduled_at,
            started_at=current.started_at if started_at is None else started_at,
            finished_at=current.finished_at if finished_at is None else finished_at,
            total=current.total if total is None else total,
            sent=current.sent if sent is None else sent,
            failed=current.failed if failed is None else failed,
        )
        self._items[broadcast_id] = updated
        return updated

    async def claim_due(self, now: datetime, limit: int = 10) -> list[Broadcast]:
        due: list[Broadcast] = []
        for item in sorted(self._items.values(), key=lambda x: x.scheduled_at or now):
            if item.status is BroadcastStatus.SCHEDULED and (
                item.scheduled_at is None or item.scheduled_at <= now
            ):
                claimed = await self.update_status(
                    item.id,
                    status=BroadcastStatus.SENDING,
                    started_at=now,
                )
                due.append(claimed)
            if len(due) >= limit:
                break
        return due

    async def claim(self, broadcast_id: str, *, now: datetime) -> Broadcast | None:
        item = self._items.get(broadcast_id)
        if item is None:
            return None
        if item.status is BroadcastStatus.SCHEDULED and (
            item.scheduled_at is None or item.scheduled_at <= now
        ):
            return await self.update_status(
                broadcast_id,
                status=BroadcastStatus.SENDING,
                started_at=now,
            )
        return item

    async def get(self, broadcast_id: str) -> Broadcast | None:
        return self._items.get(broadcast_id)

    async def list(
        self,
        *,
        limit: int = 50,
        offset: int = 0,
        statuses=None,
        query: str | None = None,
    ) -> BroadcastCollection:
        items = list(self._items.values())
        if statuses:
            statuses_set = set(statuses)
            items = [item for item in items if item.status in statuses_set]
        if query:
            needle = query.lower()
            items = [
                item
                for item in items
                if needle in item.title.lower()
                or (item.body or "").lower().find(needle) >= 0
                or (item.template_id or "").lower().find(needle) >= 0
            ]
        sliced = tuple(items[offset : offset + limit])
        counts: dict[BroadcastStatus, int] = {status: 0 for status in BroadcastStatus}
        for item in items:
            counts[item.status] = counts.get(item.status, 0) + 1
        recipient_total = sum(item.total for item in items)
        return BroadcastCollection(
            items=sliced,
            total=len(items),
            status_counts=counts,
            recipient_total=recipient_total,
        )


def _make_broadcast(
    *,
    audience: BroadcastAudience,
    status: BroadcastStatus = BroadcastStatus.SCHEDULED,
    scheduled_at: datetime | None = None,
    template_id: str | None = None,
) -> Broadcast:
    now = datetime.now(UTC)
    return Broadcast(
        id="b-1",
        title="Launch",
        body="Hello",
        template_id=template_id,
        audience=audience,
        status=status,
        created_by="ops",
        created_at=now,
        updated_at=now,
        scheduled_at=scheduled_at or (now - timedelta(minutes=5)),
        started_at=None,
        finished_at=None,
        total=0,
        sent=0,
        failed=0,
    )


@pytest.mark.asyncio
async def test_process_due_success() -> None:
    repo = _MemoryBroadcastRepo()
    broadcast = _make_broadcast(
        audience=BroadcastAudience(
            BroadcastAudienceType.EXPLICIT_USERS,
            user_ids=["u1", "u2"],
        )
    )
    repo.add(broadcast)
    delivery = _StubDelivery()
    resolver = _StubAudienceResolver(
        {BroadcastAudienceType.EXPLICIT_USERS: ["u1", "u2"]}
    )
    orchestrator = BroadcastOrchestrator(
        repo=repo,
        delivery=cast("DeliveryService", delivery),
        audience_resolver=cast("BroadcastAudienceResolver", resolver),
        template_service=None,
    )

    summaries = await orchestrator.process_due(now=datetime.now(UTC))

    assert summaries == [
        BroadcastDeliverySummary(
            broadcast_id="b-1",
            status=BroadcastStatus.SENT,
            total=2,
            sent=2,
            failed=0,
        )
    ]
    stored = await repo.get("b-1")
    assert stored is not None and stored.status is BroadcastStatus.SENT
    assert delivery.events and {event.user_id for event in delivery.events} == {
        "u1",
        "u2",
    }


@pytest.mark.asyncio
async def test_process_due_with_failures_marks_failed() -> None:
    repo = _MemoryBroadcastRepo()
    broadcast = _make_broadcast(
        audience=BroadcastAudience(
            BroadcastAudienceType.EXPLICIT_USERS,
            user_ids=["u1", "u2"],
        )
    )
    repo.add(broadcast)
    delivery = _StubDelivery(fail_ids={"u2"})
    resolver = _StubAudienceResolver(
        {BroadcastAudienceType.EXPLICIT_USERS: ["u1", "u2"]}
    )
    orchestrator = BroadcastOrchestrator(
        repo=repo,
        delivery=cast("DeliveryService", delivery),
        audience_resolver=cast("BroadcastAudienceResolver", resolver),
        template_service=None,
    )

    summaries = await orchestrator.process_due(now=datetime.now(UTC))

    assert summaries[0].status is BroadcastStatus.FAILED
    assert summaries[0].failed == 1
    stored = await repo.get("b-1")
    assert stored is not None and stored.failed == 1


@pytest.mark.asyncio
async def test_process_one_skips_not_due() -> None:
    repo = _MemoryBroadcastRepo()
    broadcast = _make_broadcast(
        audience=BroadcastAudience(
            BroadcastAudienceType.EXPLICIT_USERS,
            user_ids=["u1"],
        ),
        scheduled_at=datetime.now(UTC) + timedelta(hours=1),
    )
    repo.add(broadcast)
    delivery = _StubDelivery()
    resolver = _StubAudienceResolver({BroadcastAudienceType.EXPLICIT_USERS: ["u1"]})
    orchestrator = BroadcastOrchestrator(
        repo=repo,
        delivery=cast("DeliveryService", delivery),
        audience_resolver=cast("BroadcastAudienceResolver", resolver),
        template_service=None,
    )

    result = await orchestrator.process_one("b-1", now=datetime.now(UTC))

    assert result is None
    stored = await repo.get("b-1")
    assert stored is not None and stored.status is BroadcastStatus.SCHEDULED


@pytest.mark.asyncio
async def test_audience_resolution_failure_marks_failed() -> None:
    repo = _MemoryBroadcastRepo()
    broadcast = _make_broadcast(
        audience=BroadcastAudience(
            BroadcastAudienceType.ALL_USERS,
        )
    )
    repo.add(broadcast)
    delivery = _StubDelivery()
    orchestrator = BroadcastOrchestrator(
        repo=repo,
        delivery=cast("DeliveryService", delivery),
        audience_resolver=cast("BroadcastAudienceResolver", _FailingAudienceResolver()),
        template_service=None,
    )

    summaries = await orchestrator.process_due(now=datetime.now(UTC))

    assert summaries[0].status is BroadcastStatus.FAILED
    stored = await repo.get("b-1")
    assert stored is not None and stored.status is BroadcastStatus.FAILED


@pytest.mark.asyncio
async def test_template_lookup_used_when_present() -> None:
    repo = _MemoryBroadcastRepo()
    broadcast = _make_broadcast(
        audience=BroadcastAudience(
            BroadcastAudienceType.EXPLICIT_USERS,
            user_ids=["u1"],
        ),
        template_id="tpl-1",
    )
    repo.add(broadcast)
    delivery = _StubDelivery()
    resolver = _StubAudienceResolver({BroadcastAudienceType.EXPLICIT_USERS: ["u1"]})
    template_service = _StubTemplateService(
        {"tpl-1": _TemplateStub(slug="tpl-slug", locale="en")}
    )
    orchestrator = BroadcastOrchestrator(
        repo=repo,
        delivery=cast("DeliveryService", delivery),
        audience_resolver=cast("BroadcastAudienceResolver", resolver),
        template_service=cast("TemplateService", template_service),
    )

    await orchestrator.process_due(now=datetime.now(UTC))

    assert delivery.events and delivery.events[0].template_slug == "tpl-slug"


@pytest.mark.asyncio
async def test_template_missing_marks_failed() -> None:
    repo = _MemoryBroadcastRepo()
    broadcast = _make_broadcast(
        audience=BroadcastAudience(
            BroadcastAudienceType.EXPLICIT_USERS,
            user_ids=["u1"],
        ),
        template_id="missing",
    )
    repo.add(broadcast)
    delivery = _StubDelivery()
    resolver = _StubAudienceResolver({BroadcastAudienceType.EXPLICIT_USERS: ["u1"]})
    orchestrator = BroadcastOrchestrator(
        repo=repo,
        delivery=cast("DeliveryService", delivery),
        audience_resolver=cast("BroadcastAudienceResolver", resolver),
        template_service=cast("TemplateService", _StubTemplateService({})),
    )

    summaries = await orchestrator.process_due(now=datetime.now(UTC))

    assert summaries[0].status is BroadcastStatus.FAILED
    stored = await repo.get("b-1")
    assert stored is not None and stored.status is BroadcastStatus.FAILED
    assert not delivery.events

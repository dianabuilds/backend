from __future__ import annotations

from collections.abc import Sequence
from datetime import UTC, datetime, timedelta

import pytest

from domains.platform.notifications.application.broadcast_service import (
    BroadcastCreateInput,
    BroadcastNotFoundError,
    BroadcastService,
    BroadcastStatusError,
    BroadcastUpdateInput,
    BroadcastValidationError,
)
from domains.platform.notifications.domain.broadcast import (
    Broadcast,
    BroadcastAudience,
    BroadcastAudienceType,
    BroadcastCollection,
    BroadcastCreateModel,
    BroadcastStatus,
    BroadcastUpdateModel,
)
from domains.platform.notifications.ports import BroadcastRepo


class InMemoryBroadcastRepo(BroadcastRepo):
    def __init__(self) -> None:
        self._storage: dict[str, Broadcast] = {}

    async def create(self, payload: BroadcastCreateModel) -> Broadcast:
        identifier = f"b-{len(self._storage) + 1}"
        model = Broadcast(
            id=identifier,
            title=payload.title,
            body=payload.body,
            template_id=payload.template_id,
            audience=payload.audience,
            status=payload.status,
            created_by=payload.created_by,
            created_at=datetime.now(UTC),
            updated_at=datetime.now(UTC),
            scheduled_at=payload.scheduled_at,
            started_at=None,
            finished_at=None,
            total=0,
            sent=0,
            failed=0,
        )
        self._storage[identifier] = model
        return model

    async def update(self, broadcast_id: str, payload: BroadcastUpdateModel) -> Broadcast:
        existing = self._storage.get(broadcast_id)
        if existing is None:
            raise BroadcastNotFoundError(broadcast_id)
        updated = Broadcast(
            id=existing.id,
            title=payload.title,
            body=payload.body,
            template_id=payload.template_id,
            audience=payload.audience,
            status=payload.status,
            created_by=existing.created_by,
            created_at=existing.created_at,
            updated_at=datetime.now(UTC),
            scheduled_at=payload.scheduled_at,
            started_at=existing.started_at,
            finished_at=existing.finished_at,
            total=existing.total,
            sent=existing.sent,
            failed=existing.failed,
        )
        self._storage[broadcast_id] = updated
        return updated

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
        existing = self._storage.get(broadcast_id)
        if existing is None:
            raise BroadcastNotFoundError(broadcast_id)
        updated = Broadcast(
            id=existing.id,
            title=existing.title,
            body=existing.body,
            template_id=existing.template_id,
            audience=existing.audience,
            status=status,
            created_by=existing.created_by,
            created_at=existing.created_at,
            updated_at=datetime.now(UTC),
            scheduled_at=(scheduled_at if scheduled_at is not None else existing.scheduled_at),
            started_at=started_at if started_at is not None else existing.started_at,
            finished_at=(finished_at if finished_at is not None else existing.finished_at),
            total=total if total is not None else existing.total,
            sent=sent if sent is not None else existing.sent,
            failed=failed if failed is not None else existing.failed,
        )
        self._storage[broadcast_id] = updated
        return updated

    async def claim_due(self, now: datetime, limit: int = 10) -> list[Broadcast]:
        if limit <= 0:
            return []
        candidates = [
            item
            for item in self._storage.values()
            if item.status is BroadcastStatus.SCHEDULED
            and (item.scheduled_at is None or item.scheduled_at <= now)
        ]
        candidates.sort(key=lambda item: item.scheduled_at or now)
        claimed: list[Broadcast] = []
        for candidate in candidates[:limit]:
            claimed.append(
                await self.update_status(
                    candidate.id,
                    status=BroadcastStatus.SENDING,
                    started_at=now,
                )
            )
        return claimed

    async def claim(self, broadcast_id: str, *, now: datetime) -> Broadcast | None:
        current = self._storage.get(broadcast_id)
        if current is None:
            return None
        if current.status is BroadcastStatus.SCHEDULED and (
            current.scheduled_at is None or current.scheduled_at <= now
        ):
            return await self.update_status(
                broadcast_id,
                status=BroadcastStatus.SENDING,
                started_at=now,
            )
        return current

    async def get(self, broadcast_id: str) -> Broadcast | None:
        return self._storage.get(broadcast_id)

    async def list(
        self,
        *,
        limit: int = 50,
        offset: int = 0,
        statuses: Sequence[BroadcastStatus] | None = None,
        query: str | None = None,
    ) -> BroadcastCollection:
        items = list(self._storage.values())
        if statuses:
            statuses_set = set(statuses)
            items = [item for item in items if item.status in statuses_set]
        if query:
            pattern = query.lower()
            items = [
                item
                for item in items
                if pattern in item.title.lower()
                or (item.body or "").lower().find(pattern) >= 0
                or (item.template_id or "").lower().find(pattern) >= 0
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


def make_all_users_audience() -> BroadcastAudience:
    return BroadcastAudience(type=BroadcastAudienceType.ALL_USERS)


@pytest.mark.asyncio
async def test_create_draft_broadcast_defaults() -> None:
    repo = InMemoryBroadcastRepo()
    service = BroadcastService(repo)
    data = BroadcastCreateInput(
        title="Release Update",
        body="Patch notes",
        template_id=None,
        audience=make_all_users_audience(),
        created_by="admin",
        scheduled_at=None,
    )

    broadcast = await service.create(data)

    assert broadcast.status is BroadcastStatus.DRAFT
    assert broadcast.scheduled_at is None
    assert broadcast.body == "Patch notes"


@pytest.mark.asyncio
async def test_create_scheduled_broadcast_sets_status() -> None:
    repo = InMemoryBroadcastRepo()
    service = BroadcastService(repo)
    scheduled_at = datetime.now(UTC) + timedelta(hours=2)

    data = BroadcastCreateInput(
        title="Maintenance",
        body="Maintenance notice",
        template_id=None,
        audience=make_all_users_audience(),
        created_by="ops",
        scheduled_at=scheduled_at,
    )

    broadcast = await service.create(data)

    assert broadcast.status is BroadcastStatus.SCHEDULED
    assert broadcast.scheduled_at is not None
    assert broadcast.scheduled_at >= scheduled_at - timedelta(seconds=1)


@pytest.mark.asyncio
async def test_update_preserves_rules_and_validates() -> None:
    repo = InMemoryBroadcastRepo()
    service = BroadcastService(repo)
    created = await service.create(
        BroadcastCreateInput(
            title="Security",
            body="Initial",
            template_id=None,
            audience=make_all_users_audience(),
            created_by="secops",
        )
    )

    updated = await service.update(
        created.id,
        BroadcastUpdateInput(
            title="Security Alert",
            body="Updated message",
            template_id=None,
            audience=make_all_users_audience(),
            scheduled_at=None,
        ),
    )

    assert updated.title == "Security Alert"
    assert updated.body == "Updated message"


@pytest.mark.asyncio
async def test_send_now_requires_mutable_status() -> None:
    repo = InMemoryBroadcastRepo()
    service = BroadcastService(repo)
    created = await service.create(
        BroadcastCreateInput(
            title="Go Live",
            body="Start now",
            template_id=None,
            audience=make_all_users_audience(),
            created_by="ops",
        )
    )
    await repo.update_status(
        created.id,
        status=BroadcastStatus.SENT,
    )

    with pytest.raises(BroadcastStatusError):
        await service.send_now(created.id)


@pytest.mark.asyncio
async def test_validation_requires_body_or_template() -> None:
    repo = InMemoryBroadcastRepo()
    service = BroadcastService(repo)
    with pytest.raises(BroadcastValidationError):
        await service.create(
            BroadcastCreateInput(
                title="Empty",
                body=None,
                template_id=None,
                audience=make_all_users_audience(),
                created_by="ops",
            )
        )


@pytest.mark.asyncio
async def test_cancel_only_allowed_for_draft_or_scheduled() -> None:
    repo = InMemoryBroadcastRepo()
    service = BroadcastService(repo)
    created = await service.create(
        BroadcastCreateInput(
            title="Reminder",
            body="Reminder body",
            template_id=None,
            audience=make_all_users_audience(),
            created_by="growth",
            scheduled_at=datetime.now(UTC) + timedelta(hours=1),
        )
    )

    cancelled = await service.cancel(created.id)
    assert cancelled.status is BroadcastStatus.CANCELLED


@pytest.mark.asyncio
async def test_get_non_existing_broadcast_raises() -> None:
    repo = InMemoryBroadcastRepo()
    service = BroadcastService(repo)
    with pytest.raises(BroadcastNotFoundError):
        await service.update(
            "missing",
            BroadcastUpdateInput(
                title="Missing",
                body="missing",
                template_id=None,
                audience=make_all_users_audience(),
                scheduled_at=None,
            ),
        )

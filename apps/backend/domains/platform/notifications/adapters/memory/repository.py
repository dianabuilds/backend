from __future__ import annotations

from collections import Counter
from collections.abc import Mapping, Sequence
from datetime import UTC, datetime
from typing import Any
from uuid import uuid4

from domains.platform.notifications.domain.broadcast import (
    Broadcast,
    BroadcastCollection,
    BroadcastCreateModel,
    BroadcastStatus,
    BroadcastUpdateModel,
)
from domains.platform.notifications.models.entities import (
    ConsentAuditRecord,
    DeliveryRequirement,
    DigestMode,
    NotificationChannel,
    NotificationMatrix,
    NotificationTopic,
    PreferenceRecord,
    TopicChannelRule,
)
from domains.platform.notifications.ports import (
    BroadcastRepo,
    NotificationConsentAuditRepo,
    NotificationMatrixRepo,
    NotificationPreferenceRepo,
    TemplateRepo,
)
from domains.platform.notifications.ports_notify import INotificationRepository


def _now() -> datetime:
    return datetime.now(tz=UTC)


class InMemoryTemplateRepo(TemplateRepo):
    def __init__(self) -> None:
        self._items: dict[str, dict[str, Any]] = {}

    async def upsert(self, payload: dict[str, Any]) -> dict[str, Any]:
        identifier = str(payload.get("id") or uuid4())
        now = _now()
        stored = {
            "id": identifier,
            "slug": str(payload.get("slug") or payload.get("name") or identifier)
            .strip()
            .lower(),
            "name": str(payload.get("name") or "").strip() or identifier,
            "description": payload.get("description"),
            "subject": payload.get("subject"),
            "body": str(payload.get("body") or ""),
            "locale": (str(payload.get("locale") or "").strip().lower() or None),
            "variables": dict(payload.get("variables") or {}),
            "meta": dict(payload.get("meta") or {}),
            "created_by": payload.get("created_by"),
            "created_at": payload.get("created_at") or now,
            "updated_at": now,
        }
        self._items[identifier] = stored
        return stored

    async def list(self, limit: int = 50, offset: int = 0) -> list[dict[str, Any]]:
        values = list(self._items.values())
        values.sort(key=lambda item: (item.get("created_at") or _now()), reverse=True)
        return values[offset : offset + max(0, limit)]

    async def get(self, template_id: str) -> dict[str, Any] | None:
        return self._items.get(str(template_id))

    async def get_by_slug(self, slug: str) -> dict[str, Any] | None:
        needle = str(slug or "").strip().lower()
        for item in self._items.values():
            if item.get("slug") == needle:
                return item
        return None

    async def delete(self, template_id: str) -> None:
        self._items.pop(str(template_id), None)


class InMemoryNotificationRepository(INotificationRepository):
    def __init__(self) -> None:
        self._messages: dict[str, dict[str, Any]] = {}
        self._receipts: dict[str, dict[str, Any]] = {}
        self._event_index: dict[str, str] = {}

    async def create_and_commit(
        self,
        *,
        user_id: str,
        title: str,
        message: str,
        type_: str,
        placement: str,
        is_preview: bool = False,
        topic_key: str | None = None,
        channel_key: str | None = None,
        priority: str = "normal",
        cta_label: str | None = None,
        cta_url: str | None = None,
        meta: Mapping[str, Any] | None = None,
        event_id: str | None = None,
    ) -> dict[str, Any]:
        normalized_meta = dict(meta or {})
        now = _now()
        message_id = str(uuid4())
        receipt_id = str(uuid4())
        record = {
            "id": receipt_id,
            "user_id": str(user_id),
            "title": title,
            "message": message,
            "type": str(type_).lower() or "system",
            "placement": placement or "inbox",
            "is_preview": bool(is_preview),
            "created_at": now,
            "read_at": None,
            "topic_key": topic_key,
            "channel_key": channel_key or ("in_app" if placement == "inbox" else None),
            "priority": str(priority or "normal").lower(),
            "cta_label": cta_label,
            "cta_url": cta_url,
            "meta": normalized_meta,
            "event_id": event_id,
            "updated_at": now,
            "message_id": message_id,
        }
        if event_id and event_id in self._event_index:
            receipt_id = self._event_index[event_id]
            existing = self._receipts.get(receipt_id)
            if existing:
                existing.update(record)
                record = existing
        else:
            self._receipts[receipt_id] = record
            if event_id:
                self._event_index[event_id] = receipt_id
        self._messages[message_id] = record
        return dict(record)

    async def list_for_user(
        self,
        user_id: str,
        *,
        placement: str | None = None,
        limit: int = 50,
        offset: int = 0,
    ) -> tuple[list[dict[str, Any]], int, int]:
        filtered = [
            rec
            for rec in self._receipts.values()
            if rec["user_id"] == str(user_id)
            and (placement is None or rec["placement"] == placement)
        ]
        total = len(filtered)
        unread_total = sum(1 for rec in filtered if not rec.get("read_at"))
        priority_order = {"urgent": 0, "high": 1, "normal": 2, "low": 3}
        filtered.sort(
            key=lambda rec: (
                priority_order.get(str(rec.get("priority") or "").lower(), 4),
                rec.get("created_at", _now()),
            ),
            reverse=False,
        )
        filtered.sort(key=lambda rec: rec.get("created_at", _now()), reverse=True)
        slice_start = max(0, int(offset))
        slice_end = slice_start + max(0, int(limit))
        items = [dict(rec) for rec in filtered[slice_start:slice_end]]
        return items, total, unread_total

    async def mark_read(self, user_id: str, notif_id: str) -> dict[str, Any] | None:
        record = self._receipts.get(str(notif_id))
        if record is None or record["user_id"] != str(user_id):
            return None
        if record.get("read_at") is None:
            record["read_at"] = _now()
            record["updated_at"] = record["read_at"]
        return dict(record)


class InMemoryNotificationConfigRepository:
    def __init__(self) -> None:
        self._store: dict[str, dict[str, Any]] = {}

    async def get_retention(self) -> dict[str, Any] | None:
        record = self._store.get("retention")
        if record is None:
            return None
        return dict(record)

    async def upsert_retention(
        self,
        *,
        retention_days: int | None,
        max_per_user: int | None,
        actor_id: str | None,
    ) -> dict[str, Any]:
        record = {
            "retention_days": retention_days,
            "max_per_user": max_per_user,
            "updated_at": _now().isoformat(),
            "updated_by": actor_id,
        }
        self._store["retention"] = record
        return dict(record)


class InMemoryBroadcastRepo(BroadcastRepo):
    def __init__(self) -> None:
        self._items: dict[str, Broadcast] = {}
        self._counter = 0

    def _next_id(self) -> str:
        self._counter += 1
        return f"broadcast-{self._counter}"

    async def create(self, payload: BroadcastCreateModel) -> Broadcast:
        identifier = self._next_id()
        now = _now()
        broadcast = Broadcast(
            id=identifier,
            title=payload.title,
            body=payload.body,
            template_id=payload.template_id,
            audience=payload.audience,
            status=payload.status,
            created_by=payload.created_by,
            created_at=now,
            updated_at=now,
            scheduled_at=payload.scheduled_at,
            started_at=None,
            finished_at=None,
            total=0,
            sent=0,
            failed=0,
        )
        self._items[identifier] = broadcast
        return broadcast

    async def update(
        self, broadcast_id: str, payload: BroadcastUpdateModel
    ) -> Broadcast:
        existing = self._items.get(broadcast_id)
        if existing is None:
            raise RuntimeError(f"broadcast {broadcast_id} not found")
        updated = Broadcast(
            id=existing.id,
            title=payload.title,
            body=payload.body,
            template_id=payload.template_id,
            audience=payload.audience,
            status=payload.status,
            created_by=existing.created_by,
            created_at=existing.created_at,
            updated_at=_now(),
            scheduled_at=payload.scheduled_at,
            started_at=existing.started_at,
            finished_at=existing.finished_at,
            total=existing.total,
            sent=existing.sent,
            failed=existing.failed,
        )
        self._items[broadcast_id] = updated
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
        existing = self._items.get(broadcast_id)
        if existing is None:
            raise RuntimeError(f"broadcast {broadcast_id} not found")
        updated = Broadcast(
            id=existing.id,
            title=existing.title,
            body=existing.body,
            template_id=existing.template_id,
            audience=existing.audience,
            status=status,
            created_by=existing.created_by,
            created_at=existing.created_at,
            updated_at=_now(),
            scheduled_at=(
                scheduled_at if scheduled_at is not None else existing.scheduled_at
            ),
            started_at=started_at if started_at is not None else existing.started_at,
            finished_at=(
                finished_at if finished_at is not None else existing.finished_at
            ),
            total=total if total is not None else existing.total,
            sent=sent if sent is not None else existing.sent,
            failed=failed if failed is not None else existing.failed,
        )
        self._items[broadcast_id] = updated
        return updated

    async def claim_due(self, now: datetime, limit: int = 10) -> list[Broadcast]:
        candidates = [
            item
            for item in self._items.values()
            if item.status is BroadcastStatus.SCHEDULED
            and (item.scheduled_at is None or item.scheduled_at <= now)
        ]
        candidates.sort(key=lambda item: item.scheduled_at or now)
        claimed: list[Broadcast] = []
        for broadcast in candidates[: max(0, limit)]:
            claimed.append(
                await self.update_status(
                    broadcast.id,
                    status=BroadcastStatus.SENDING,
                    started_at=now,
                )
            )
        return claimed

    async def claim(self, broadcast_id: str, *, now: datetime) -> Broadcast | None:
        existing = self._items.get(broadcast_id)
        if existing is None:
            return None
        if existing.status is not BroadcastStatus.SCHEDULED:
            return None
        return await self.update_status(
            broadcast_id,
            status=BroadcastStatus.SENDING,
            started_at=now,
        )

    async def get(self, broadcast_id: str) -> Broadcast | None:
        return self._items.get(broadcast_id)

    async def list(
        self,
        *,
        limit: int = 50,
        offset: int = 0,
        statuses: Sequence[BroadcastStatus] | None = None,
        query: str | None = None,
    ) -> BroadcastCollection:
        items = list(self._items.values())
        if statuses:
            allowed = {status for status in statuses}
            items = [item for item in items if item.status in allowed]
        if query:
            needle = query.strip().lower()
            items = [
                item
                for item in items
                if needle in item.title.lower()
                or (item.body or "").lower().find(needle) >= 0
            ]
        items.sort(key=lambda item: item.updated_at, reverse=True)
        total = len(items)
        page = tuple(items[offset : offset + limit])
        counts = Counter(item.status for item in items)
        status_counts = {status: counts.get(status, 0) for status in BroadcastStatus}
        recipient_total = sum(item.total for item in items)
        return BroadcastCollection(
            items=page,
            total=total,
            status_counts=status_counts,
            recipient_total=recipient_total,
        )


class InMemoryNotificationMatrixRepo(NotificationMatrixRepo):
    def __init__(self, matrix: NotificationMatrix | None = None) -> None:
        self._matrix = matrix or self._default_matrix()

    async def load(self, *, use_cache: bool = True) -> NotificationMatrix:
        return self._matrix

    @staticmethod
    def _default_matrix() -> NotificationMatrix:
        channel = NotificationChannel(
            key="in_app",
            display_name="In-App",
            category="system",
            supports_digest=False,
        )
        topic = NotificationTopic(
            key="general.updates",
            category="general",
            display_name="General updates",
        )
        rule = TopicChannelRule(
            topic_key=topic.key,
            channel_key=channel.key,
            delivery=DeliveryRequirement.DEFAULT_ON,
            default_opt_in=True,
            default_digest=DigestMode.INSTANT,
        )
        return NotificationMatrix(
            topics={topic.key: topic},
            channels={channel.key: channel},
            rules={(topic.key, channel.key): rule},
            version=1,
        )


class InMemoryNotificationPreferenceRepo(NotificationPreferenceRepo):
    def __init__(self) -> None:
        self._storage: dict[tuple[str, str, str], PreferenceRecord] = {}

    async def list_for_user(self, user_id: str) -> list[PreferenceRecord]:
        return [
            record
            for (uid, _, _), record in self._storage.items()
            if uid == str(user_id)
        ]

    async def replace_for_user(
        self, user_id: str, records: Sequence[PreferenceRecord]
    ) -> None:
        keys_to_remove = [key for key in self._storage if key[0] == str(user_id)]
        for key in keys_to_remove:
            self._storage.pop(key, None)
        for record in records:
            key = (str(user_id), record.topic_key, record.channel_key)
            self._storage[key] = record


class InMemoryNotificationConsentAuditRepo(NotificationConsentAuditRepo):
    def __init__(self) -> None:
        self._records: list[ConsentAuditRecord] = []

    async def append_many(self, records: Sequence[ConsentAuditRecord]) -> None:
        self._records.extend(records)

    @property
    def records(self) -> Sequence[ConsentAuditRecord]:
        return tuple(self._records)


__all__ = [
    "InMemoryTemplateRepo",
    "InMemoryNotificationRepository",
    "InMemoryBroadcastRepo",
    "InMemoryNotificationMatrixRepo",
    "InMemoryNotificationPreferenceRepo",
    "InMemoryNotificationConsentAuditRepo",
]

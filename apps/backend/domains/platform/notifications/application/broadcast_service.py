from __future__ import annotations

from collections.abc import Callable, Iterable
from dataclasses import dataclass
from datetime import UTC, datetime

from domains.platform.notifications.domain.broadcast import (
    Broadcast,
    BroadcastAudience,
    BroadcastCollection,
    BroadcastCreateModel,
    BroadcastStatus,
    BroadcastUpdateModel,
)
from domains.platform.notifications.ports import BroadcastRepo


class BroadcastServiceError(RuntimeError):
    """Base class for broadcast-related service errors."""


class BroadcastNotFoundError(BroadcastServiceError):
    """Raised when a broadcast requested by id is missing."""


class BroadcastValidationError(BroadcastServiceError):
    """Raised when input data fails validation rules."""


class BroadcastStatusError(BroadcastServiceError):
    """Raised on illegal status transitions."""


@dataclass(frozen=True)
class BroadcastCreateInput:
    title: str
    body: str | None
    template_id: str | None
    audience: BroadcastAudience
    created_by: str
    scheduled_at: datetime | None = None


@dataclass(frozen=True)
class BroadcastUpdateInput:
    title: str
    body: str | None
    template_id: str | None
    audience: BroadcastAudience
    scheduled_at: datetime | None


class BroadcastService:
    """Application service orchestrating broadcast lifecycle."""

    def __init__(
        self,
        repo: BroadcastRepo,
        *,
        clock: Callable[[], datetime] | None = None,
    ) -> None:
        self._repo = repo
        self._clock = clock or (lambda: datetime.now(UTC))

    async def create(self, data: BroadcastCreateInput) -> Broadcast:
        self._validate_title(data.title)
        self._validate_content(body=data.body, template_id=data.template_id)
        data.audience.validate()

        scheduled_at = self._normalize_schedule(data.scheduled_at)
        status = self._initial_status(scheduled_at)

        payload = BroadcastCreateModel(
            title=data.title.strip(),
            body=self._normalize_body(data.body),
            template_id=self._normalize_template(data.template_id),
            audience=data.audience,
            status=status,
            created_by=data.created_by,
            scheduled_at=scheduled_at,
        )
        return await self._repo.create(payload)

    async def update(self, broadcast_id: str, data: BroadcastUpdateInput) -> Broadcast:
        broadcast = await self._get_existing(broadcast_id)
        self._ensure_mutable(broadcast.status)

        self._validate_title(data.title)
        self._validate_content(body=data.body, template_id=data.template_id)
        data.audience.validate()

        scheduled_at = self._normalize_schedule(data.scheduled_at)
        status = self._status_after_edit(broadcast.status, scheduled_at)

        payload = BroadcastUpdateModel(
            title=data.title.strip(),
            body=self._normalize_body(data.body),
            template_id=self._normalize_template(data.template_id),
            audience=data.audience,
            status=status,
            scheduled_at=scheduled_at,
        )
        return await self._repo.update(broadcast_id, payload)

    async def schedule(self, broadcast_id: str, scheduled_at: datetime) -> Broadcast:
        broadcast = await self._get_existing(broadcast_id)
        self._ensure_mutable(broadcast.status)
        normalized = self._normalize_schedule(scheduled_at)
        return await self._repo.update_status(
            broadcast_id,
            status=BroadcastStatus.SCHEDULED,
            scheduled_at=normalized,
        )

    async def send_now(self, broadcast_id: str) -> Broadcast:
        broadcast = await self._get_existing(broadcast_id)
        self._ensure_mutable(broadcast.status)
        now = self._clock()
        return await self._repo.update_status(
            broadcast_id,
            status=BroadcastStatus.SCHEDULED,
            scheduled_at=now,
        )

    async def cancel(self, broadcast_id: str) -> Broadcast:
        broadcast = await self._get_existing(broadcast_id)
        if broadcast.status not in {BroadcastStatus.DRAFT, BroadcastStatus.SCHEDULED}:
            raise BroadcastStatusError(
                f"Cannot cancel broadcast in status {broadcast.status.value}"
            )
        return await self._repo.update_status(
            broadcast_id,
            status=BroadcastStatus.CANCELLED,
            scheduled_at=None,
        )

    async def mark_sending(
        self,
        broadcast_id: str,
        *,
        total: int | None = None,
    ) -> Broadcast:
        now = self._clock()
        return await self._repo.update_status(
            broadcast_id,
            status=BroadcastStatus.SENDING,
            started_at=now,
            total=total,
        )

    async def mark_sent(
        self,
        broadcast_id: str,
        *,
        total: int,
        sent: int,
        failed: int,
    ) -> Broadcast:
        now = self._clock()
        return await self._repo.update_status(
            broadcast_id,
            status=BroadcastStatus.SENT,
            finished_at=now,
            total=total,
            sent=sent,
            failed=failed,
        )

    async def mark_failed(
        self,
        broadcast_id: str,
        *,
        total: int | None = None,
        sent: int | None = None,
        failed: int | None = None,
    ) -> Broadcast:
        now = self._clock()
        return await self._repo.update_status(
            broadcast_id,
            status=BroadcastStatus.FAILED,
            finished_at=now,
            total=total,
            sent=sent,
            failed=failed,
        )

    async def get(self, broadcast_id: str) -> Broadcast | None:
        return await self._repo.get(broadcast_id)

    async def list(
        self,
        *,
        limit: int = 50,
        offset: int = 0,
        statuses: Iterable[BroadcastStatus] | None = None,
        query: str | None = None,
    ) -> BroadcastCollection:
        normalized_query = (query or "").strip() or None
        statuses_seq = tuple(statuses) if statuses else None
        return await self._repo.list(
            limit=limit, offset=offset, statuses=statuses_seq, query=normalized_query
        )

    async def _get_existing(self, broadcast_id: str) -> Broadcast:
        broadcast = await self._repo.get(broadcast_id)
        if broadcast is None:
            raise BroadcastNotFoundError(f"Broadcast {broadcast_id} not found")
        return broadcast

    @staticmethod
    def _ensure_mutable(status: BroadcastStatus) -> None:
        if status not in {BroadcastStatus.DRAFT, BroadcastStatus.SCHEDULED}:
            raise BroadcastStatusError(f"Cannot edit broadcast in status {status.value}")

    @staticmethod
    def _validate_title(title: str) -> None:
        if not title or not title.strip():
            raise BroadcastValidationError("Title cannot be empty")

    @staticmethod
    def _validate_content(*, body: str | None, template_id: str | None) -> None:
        if (body is None or not body.strip()) and not template_id:
            raise BroadcastValidationError("Either body or template_id must be provided")

    @staticmethod
    def _normalize_body(body: str | None) -> str | None:
        if body is None:
            return None
        normalized = body.strip()
        return normalized or None

    @staticmethod
    def _normalize_template(template_id: str | None) -> str | None:
        if template_id is None:
            return None
        normalized = template_id.strip()
        return normalized or None

    def _normalize_schedule(self, scheduled_at: datetime | None) -> datetime | None:
        if scheduled_at is None:
            return None
        if scheduled_at.tzinfo is None:
            raise BroadcastValidationError("scheduled_at must be timezone-aware")
        now = self._clock()
        if scheduled_at <= now:
            return now
        return scheduled_at

    @staticmethod
    def _initial_status(scheduled_at: datetime | None) -> BroadcastStatus:
        if scheduled_at is not None:
            return BroadcastStatus.SCHEDULED
        return BroadcastStatus.DRAFT

    @staticmethod
    def _status_after_edit(
        current_status: BroadcastStatus, scheduled_at: datetime | None
    ) -> BroadcastStatus:
        if scheduled_at is not None:
            return BroadcastStatus.SCHEDULED
        if current_status is BroadcastStatus.SCHEDULED:
            return BroadcastStatus.DRAFT
        return current_status


__all__ = [
    "BroadcastCreateInput",
    "BroadcastNotFoundError",
    "BroadcastService",
    "BroadcastServiceError",
    "BroadcastStatusError",
    "BroadcastUpdateInput",
    "BroadcastValidationError",
]

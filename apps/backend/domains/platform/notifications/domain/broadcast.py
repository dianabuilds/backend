from __future__ import annotations

from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from typing import Any


class BroadcastStatus(str, Enum):
    """Lifecycle status for broadcast notifications."""

    DRAFT = "draft"
    SCHEDULED = "scheduled"
    SENDING = "sending"
    SENT = "sent"
    FAILED = "failed"
    CANCELLED = "cancelled"


class BroadcastAudienceType(str, Enum):
    """Audience modes supported by the broadcast product."""

    ALL_USERS = "all_users"
    SEGMENT = "segment"
    EXPLICIT_USERS = "explicit_users"


@dataclass(frozen=True)
class BroadcastAudience:
    """Normalized representation of an audience target."""

    type: BroadcastAudienceType
    filters: Mapping[str, Any] | None = None
    user_ids: Sequence[str] | None = None

    def validate(self) -> None:
        """Validate internal invariants and raise ValueError if something is off."""

        if self.type is BroadcastAudienceType.ALL_USERS:
            if self.filters or self.user_ids:
                raise ValueError("all_users audience cannot carry filters or user ids")
            return

        if self.type is BroadcastAudienceType.SEGMENT:
            if not self.filters:
                raise ValueError("segment audience requires non-empty filters")
            if self.user_ids:
                raise ValueError("segment audience cannot include explicit user ids")
            return

        if self.type is BroadcastAudienceType.EXPLICIT_USERS:
            if not self.user_ids:
                raise ValueError("explicit_users audience requires user ids")
            if self.filters:
                raise ValueError("explicit_users audience cannot include filters")
            return

        raise ValueError(f"unsupported audience type: {self.type}")


@dataclass(frozen=True)
class Broadcast:
    """Read model returned to services and API layers."""

    id: str
    title: str
    body: str | None
    template_id: str | None
    audience: BroadcastAudience
    status: BroadcastStatus
    created_by: str
    created_at: datetime
    updated_at: datetime
    scheduled_at: datetime | None
    started_at: datetime | None
    finished_at: datetime | None
    total: int
    sent: int
    failed: int


@dataclass(frozen=True)
class BroadcastDraft:
    """Payload used when creating or editing a draft broadcast."""

    title: str
    body: str | None
    template_id: str | None
    audience: BroadcastAudience
    scheduled_at: datetime | None = None


@dataclass(frozen=True)
class BroadcastCreateModel:
    """Write model passed to repositories when creating a broadcast."""

    title: str
    body: str | None
    template_id: str | None
    audience: BroadcastAudience
    status: BroadcastStatus
    created_by: str
    scheduled_at: datetime | None


@dataclass(frozen=True)
class BroadcastUpdateModel:
    """Write model for repository updates of an existing broadcast."""

    title: str
    body: str | None
    template_id: str | None
    audience: BroadcastAudience
    status: BroadcastStatus
    scheduled_at: datetime | None


@dataclass(frozen=True)
class BroadcastCollection:
    """Page of broadcasts with aggregate metadata."""

    items: tuple[Broadcast, ...]
    total: int
    status_counts: Mapping[BroadcastStatus, int]
    recipient_total: int


__all__ = [
    "Broadcast",
    "BroadcastAudience",
    "BroadcastAudienceType",
    "BroadcastCreateModel",
    "BroadcastDraft",
    "BroadcastStatus",
    "BroadcastUpdateModel",
    "BroadcastCollection",
]

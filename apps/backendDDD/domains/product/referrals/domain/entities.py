from __future__ import annotations

from dataclasses import dataclass, field
from datetime import UTC, datetime
from typing import Any


def utcnow() -> datetime:
    return datetime.now(tz=UTC)


@dataclass
class ReferralCode:
    id: str
    owner_user_id: str
    code: str
    active: bool = True
    uses_count: int = 0
    created_at: datetime = field(default_factory=utcnow)


@dataclass
class ReferralEvent:
    id: str
    code_id: str | None
    code: str | None
    referrer_user_id: str | None
    referee_user_id: str
    event_type: str
    occurred_at: datetime = field(default_factory=utcnow)
    meta: dict[str, Any] = field(default_factory=dict)

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import UTC, datetime
from typing import Any


def utcnow() -> datetime:
    return datetime.now(tz=UTC)


@dataclass
class Achievement:
    id: str
    code: str
    title: str
    description: str | None = None
    icon: str | None = None
    visible: bool = True
    condition: dict[str, Any] = field(default_factory=dict)
    created_by_user_id: str | None = None
    updated_by_user_id: str | None = None
    created_at: datetime = field(default_factory=utcnow)
    updated_at: datetime = field(default_factory=utcnow)


@dataclass
class UserAchievement:
    user_id: str
    achievement_id: str
    unlocked_at: datetime = field(default_factory=utcnow)

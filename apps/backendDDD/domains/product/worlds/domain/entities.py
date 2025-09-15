from __future__ import annotations

from dataclasses import dataclass, field
from datetime import UTC, datetime
from typing import Any


def utcnow() -> datetime:
    return datetime.now(tz=UTC)


@dataclass
class WorldTemplate:
    id: str
    workspace_id: str
    title: str
    locale: str | None = None
    description: str | None = None
    meta: dict[str, Any] = field(default_factory=dict)
    created_at: datetime = field(default_factory=utcnow)
    updated_at: datetime = field(default_factory=utcnow)
    created_by_user_id: str | None = None
    updated_by_user_id: str | None = None


@dataclass
class Character:
    id: str
    world_id: str
    name: str
    role: str | None = None
    description: str | None = None
    traits: dict[str, Any] = field(default_factory=dict)
    created_at: datetime = field(default_factory=utcnow)
    updated_at: datetime = field(default_factory=utcnow)
    created_by_user_id: str | None = None
    updated_by_user_id: str | None = None

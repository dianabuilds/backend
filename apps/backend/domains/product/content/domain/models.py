from __future__ import annotations

import enum
from collections.abc import Mapping
from dataclasses import dataclass
from datetime import datetime
from typing import Any
from uuid import UUID


class HomeConfigStatus(str, enum.Enum):
    DRAFT = "draft"
    PUBLISHED = "published"


JSONDict = dict[str, Any]


@dataclass(slots=True)
class HomeConfig:
    id: UUID
    slug: str
    version: int
    status: HomeConfigStatus
    data: Mapping[str, Any]
    created_by: str | None
    updated_by: str | None
    created_at: datetime
    updated_at: datetime
    published_at: datetime | None
    draft_of: UUID | None


@dataclass(slots=True)
class HomeConfigAudit:
    id: UUID
    config_id: UUID
    version: int
    action: str
    actor: str | None
    actor_team: str | None
    comment: str | None
    data: Mapping[str, Any] | None
    diff: list[dict[str, Any]] | None
    created_at: datetime


@dataclass(slots=True)
class HomeConfigHistoryEntry:
    config: HomeConfig
    actor: str | None
    actor_team: str | None
    comment: str | None
    created_at: datetime
    diff: list[dict[str, Any]] | None


__all__ = [
    "HomeConfig",
    "HomeConfigAudit",
    "HomeConfigHistoryEntry",
    "HomeConfigStatus",
    "JSONDict",
]

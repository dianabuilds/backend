from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime


@dataclass(frozen=True)
class TagListItem:
    id: str
    slug: str
    name: str
    created_at: datetime
    is_hidden: bool
    usage_count: int = 0
    aliases_count: int = 0


@dataclass(frozen=True)
class AliasView:
    id: str
    tag_id: str
    alias: str
    type: str
    created_at: datetime


@dataclass(frozen=True)
class BlacklistItem:
    slug: str
    reason: str | None
    created_at: datetime

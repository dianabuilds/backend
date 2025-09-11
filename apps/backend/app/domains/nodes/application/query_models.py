from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Any
from uuid import UUID

from app.schemas.nodes_common import Status


@dataclass
class NodeFilterSpec:
    author_id: UUID | None = None
    status: Status | None = None
    is_visible: bool | None = True
    premium_only: bool | None = None
    recommendable: bool | None = None
    created_from: datetime | None = None
    created_to: datetime | None = None
    updated_from: datetime | None = None
    updated_to: datetime | None = None
    # updated_desc | created_desc | created_asc | views_desc
    sort: str | None = "updated_desc"
    q: str | None = None
    min_views: int | None = None


@dataclass
class PageRequest:
    offset: int = 0
    limit: int = 50


@dataclass
class QueryContext:
    user: Any | None = None
    is_admin: bool = False

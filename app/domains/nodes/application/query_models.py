from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import List, Optional, Any
from uuid import UUID


@dataclass
class NodeFilterSpec:
    tags: Optional[List[str]] = None
    match: str = "any"
    author_id: Optional[UUID] = None
    is_public: Optional[bool] = None
    is_visible: Optional[bool] = True
    premium_only: Optional[bool] = None
    recommendable: Optional[bool] = None
    created_from: Optional[datetime] = None
    created_to: Optional[datetime] = None
    updated_from: Optional[datetime] = None
    updated_to: Optional[datetime] = None
    sort: Optional[str] = None  # created_desc | created_asc | views_desc | reactions_desc
    q: Optional[str] = None
    min_views: Optional[int] = None
    min_reactions: Optional[int] = None


@dataclass
class PageRequest:
    offset: int = 0
    limit: int = 50


@dataclass
class QueryContext:
    user: Any | None = None
    is_admin: bool = False

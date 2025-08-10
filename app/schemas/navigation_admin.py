from __future__ import annotations

from typing import Any, Literal
from uuid import UUID

from pydantic import BaseModel


class NavigationRunRequest(BaseModel):
    node_slug: str
    user_id: UUID | None = None


class NavigationCacheSetRequest(BaseModel):
    node_slug: str
    user_id: UUID | None = None
    payload: dict[str, Any]


class NavigationCacheInvalidateRequest(BaseModel):
    scope: Literal["node", "user", "all"]
    node_slug: str | None = None
    user_id: UUID | None = None

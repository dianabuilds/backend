from __future__ import annotations

from uuid import UUID

from pydantic import BaseModel


class NavigationNodeProblem(BaseModel):
    node_id: UUID
    slug: str
    title: str | None = None
    views: int
    transitions: int
    ctr: float
    dead_end: bool
    cycle: bool

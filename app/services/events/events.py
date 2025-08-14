"""Domain event definitions."""
from __future__ import annotations

from dataclasses import dataclass
from uuid import UUID

from .base import Event


@dataclass(slots=True, kw_only=True)
class NodeCreated(Event):
    node_id: UUID
    slug: str
    author_id: UUID


@dataclass(slots=True, kw_only=True)
class NodeUpdated(Event):
    node_id: UUID
    slug: str
    author_id: UUID
    tags_changed: bool = False

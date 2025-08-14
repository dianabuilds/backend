"""Core primitives for domain events."""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from typing import Protocol, runtime_checkable
from uuid import UUID, uuid4


@dataclass(slots=True)
class Event:
    """Base event with common metadata."""

    event_id: UUID = field(default_factory=uuid4)
    version: int = 1
    correlation_id: str | None = None
    occurred_at: datetime = field(default_factory=datetime.utcnow)


@runtime_checkable
class EventHandler(Protocol):
    """Protocol for event handlers."""

    async def handle(self, event: Event) -> None:  # pragma: no cover - interface
        ...

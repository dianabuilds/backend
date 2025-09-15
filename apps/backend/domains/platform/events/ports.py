from __future__ import annotations

from collections.abc import Callable
from typing import Protocol, runtime_checkable

# Topic name convention example: "profile.updated.v1"
Handler = Callable[[str, dict], None]


@runtime_checkable
class OutboxPublisher(Protocol):
    def publish(self, topic: str, payload: dict, key: str | None = None) -> None: ...


@runtime_checkable
class EventBus(Protocol):
    def subscribe(self, topic: str, handler: Handler) -> None: ...
    def run(self, block_ms: int | None = None, count: int | None = None) -> None: ...


__all__ = ["OutboxPublisher", "EventBus", "Handler"]

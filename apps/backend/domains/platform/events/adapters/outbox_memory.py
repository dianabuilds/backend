from __future__ import annotations

from collections import deque
from collections.abc import Iterable
from typing import Any

from domains.platform.events.ports import OutboxPublisher


class InMemoryOutbox(OutboxPublisher):
    """Stores published events in memory for assertions during tests."""

    def __init__(self) -> None:
        self._events: deque[tuple[str, dict[str, Any], str | None]] = deque()

    def publish(
        self, topic: str, payload: dict[str, Any], key: str | None = None
    ) -> None:
        self._events.append((topic, dict(payload), key))

    def drain(self) -> Iterable[tuple[str, dict[str, Any], str | None]]:
        while self._events:
            yield self._events.popleft()

    def clear(self) -> None:
        self._events.clear()


__all__ = ["InMemoryOutbox"]

from __future__ import annotations

from domains.platform.events.ports import OutboxPublisher


class MemoryOutbox(OutboxPublisher):
    """In-memory outbox for tests/dev.

    Stores published events in a list for inspection. Does not deliver anywhere.
    """

    def __init__(self) -> None:
        self.events: list[tuple[str, dict, str | None]] = []

    def publish(self, topic: str, payload: dict, key: str | None = None) -> None:
        self.events.append((str(topic), dict(payload), key))


__all__ = ["MemoryOutbox"]

from __future__ import annotations

from apps.backendDDD.domains.platform.events.ports import EventBus, Handler


class InMemoryEventBus(EventBus):
    def __init__(self) -> None:
        self._routes: dict[str, list[Handler]] = {}

    def subscribe(self, topic: str, handler: Handler) -> None:
        self._routes.setdefault(topic, []).append(handler)

    def run(
        self, block_ms: int | None = None, count: int | None = None
    ) -> None:  # pragma: no cover - simple
        # No background loop; in tests you can call handlers manually if needed.
        pass

    # Helper to trigger in tests
    def emit(self, topic: str, payload: dict) -> None:
        for h in self._routes.get(topic, []):
            h(topic, payload)


__all__ = ["InMemoryEventBus"]

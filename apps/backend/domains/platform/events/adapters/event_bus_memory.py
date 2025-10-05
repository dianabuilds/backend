from __future__ import annotations

import logging
from collections import defaultdict
from typing import Any

from domains.platform.events.ports import EventBus, Handler

logger = logging.getLogger(__name__)


class InMemoryEventBus(EventBus):
    """Minimal event bus for tests that executes handlers in-process."""

    def __init__(self) -> None:
        self._routes: dict[str, list[Handler]] = defaultdict(list)

    def subscribe(self, topic: str, handler: Handler) -> None:
        self._routes[topic].append(handler)

    def emit(self, topic: str, payload: dict[str, Any]) -> None:
        handlers = list(self._routes.get(topic, ()))
        for handler in handlers:
            try:
                handler(topic, payload)
            except Exception:
                logger.exception(
                    "in_memory_event_handler_failed", extra={"topic": topic}
                )

    def run(self, block_ms: int | None = None, count: int | None = None) -> None:
        # Nothing to do; handlers are invoked synchronously by emit().
        return None

    def stop(self) -> None:
        self._routes.clear()


__all__ = ["InMemoryEventBus"]

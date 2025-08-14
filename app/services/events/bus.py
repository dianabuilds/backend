"""Event bus interfaces and in-memory implementation."""
from __future__ import annotations

import asyncio
import logging
import time
from collections import defaultdict
import os
from typing import Awaitable, Callable, Dict, List, Type
from uuid import UUID

from .base import Event, EventHandler

logger = logging.getLogger(__name__)

HandlerFunc = Callable[[Event], Awaitable[None]]


class EventBus:
    """Interface for publishing events."""

    def subscribe(self, event_type: Type[Event], handler: HandlerFunc) -> None:  # pragma: no cover - interface
        ...

    async def publish(self, event: Event) -> None:  # pragma: no cover - interface
        ...


class InMemoryEventBus(EventBus):
    """Simple in-memory event bus using asyncio tasks."""

    def __init__(self, max_retries: int = 3) -> None:
        self._handlers: Dict[Type[Event], List[HandlerFunc]] = defaultdict(list)
        self._processed: Dict[HandlerFunc, set[UUID]] = defaultdict(set)
        self._max_retries = max_retries

    def subscribe(self, event_type: Type[Event], handler: HandlerFunc) -> None:
        self._handlers[event_type].append(handler)

    async def publish(self, event: Event) -> None:
        handlers = list(self._handlers.get(type(event), []))
        if os.environ.get("TESTING") == "True":
            for handler in handlers:
                await self._run_handler(handler, event)
        else:
            for handler in handlers:
                asyncio.create_task(self._run_handler(handler, event))

    async def _run_handler(self, handler: HandlerFunc, event: Event) -> None:
        if event.event_id in self._processed[handler]:
            logger.debug("Event %s already processed by %s", event.event_id, handler)
            return
        attempt = 0
        while True:
            try:
                start = time.perf_counter()
                await handler(event)
                duration = (time.perf_counter() - start) * 1000
                logger.info(
                    "Handled event %s by %s in %.2fms", type(event).__name__, handler.__name__, duration
                )
                self._processed[handler].add(event.event_id)
                break
            except Exception as exc:  # pragma: no cover - log and retry
                attempt += 1
                if attempt >= self._max_retries:
                    logger.exception("Handler %s failed after %d attempts", handler.__name__, attempt)
                    break
                delay = 2 ** attempt
                logger.warning(
                    "Handler %s error %s on attempt %d, retrying in %ds", handler.__name__, exc, attempt, delay
                )
                await asyncio.sleep(delay)


# global singleton
_event_bus: InMemoryEventBus | None = None


def get_event_bus() -> InMemoryEventBus:
    global _event_bus
    if _event_bus is None:
        _event_bus = InMemoryEventBus()
    return _event_bus

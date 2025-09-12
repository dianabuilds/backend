from __future__ import annotations

import asyncio
import logging
import time
from collections import deque
from collections.abc import Awaitable, Callable
from typing import Any
from uuid import uuid4

logger = logging.getLogger(__name__)


async def _noop(_event: Any) -> None:
    return None


class EventBus:
    def __init__(self, processed_maxlen: int = 1024) -> None:
        self._handlers: dict[type, list[Callable[[Any], Awaitable[None]]]] = {}
        self._processed: deque[str] = deque()
        self._processed_set: set[str] = set()
        self._processed_maxlen = processed_maxlen

    def subscribe(
        self,
        event_type: type,
        handler: Callable[[Any], Awaitable[None]],
    ) -> None:
        self._handlers.setdefault(event_type, []).append(handler)

    async def publish(self, event: Any) -> None:
        event_id = getattr(event, "id", None)
        if event_id is None:
            event_id = uuid4().hex
            try:
                event.id = event_id  # type: ignore[attr-defined]
            except Exception:
                pass
        if event_id in self._processed_set:
            return
        self._processed.append(event_id)
        self._processed_set.add(event_id)
        if len(self._processed) > self._processed_maxlen:
            old = self._processed.popleft()
            self._processed_set.discard(old)
        handlers = self._handlers.get(type(event), [])
        for h in handlers:
            attempts = 0
            total_ms = 0.0
            success = False
            while True:
                start = time.perf_counter()
                try:
                    await h(event)
                    success = True
                    break
                except Exception:
                    attempts += 1
                    if attempts >= 3:
                        logger.exception("event handler failed after %s attempts", attempts)
                        break
                    await asyncio.sleep(0)
                finally:
                    end = time.perf_counter()
                    total_ms += (end - start) * 1000
            # Optional metrics hook via log; domains can record real metrics
            logger.debug(
                "event handled: %s by=%s success=%s time_ms=%.2f",
                type(event).__name__,
                getattr(h, "__name__", h.__class__.__name__),
                success,
                total_ms,
            )


_bus = EventBus()


def get_event_bus() -> EventBus:
    return _bus


def register_handlers() -> None:
    """Compatibility shim; does nothing in kernel.

    Domain packages should register their own handlers during bootstrap.
    """
    return None


__all__ = ["EventBus", "get_event_bus", "register_handlers"]


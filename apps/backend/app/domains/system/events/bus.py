from __future__ import annotations

import asyncio
import logging
import time
from collections import deque
from collections.abc import Awaitable, Callable
from typing import Any
from uuid import uuid4

from app.domains.telemetry.application.event_metrics_facade import event_metrics

from .handlers import handlers
from .models import EVENT_METRIC_NAMES, NodeCreated, NodePublished, NodeUpdated

logger = logging.getLogger(__name__)


async def _record_metric(event: Any) -> None:
    name = EVENT_METRIC_NAMES.get(type(event))
    if not name:
        return
    ws = getattr(event, "workspace_id", None)
    event_metrics.inc(name, str(ws) if ws is not None else None)


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
            event.id = event_id
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
                        logger.exception(
                            "event handler failed after %s attempts", attempts
                        )
                        break
                    await asyncio.sleep(0)
                finally:
                    end = time.perf_counter()
                    total_ms += (end - start) * 1000
            name = EVENT_METRIC_NAMES.get(type(event), type(event).__name__)
            event_metrics.record_handler(
                name,
                getattr(h, "__name__", h.__class__.__name__),
                success,
                total_ms,
            )


_bus = EventBus()
_registered = False


def register_handlers() -> None:
    global _registered
    if _registered:
        return
    for ev in EVENT_METRIC_NAMES:
        _bus.subscribe(ev, _record_metric)
    _bus.subscribe(NodeCreated, handlers.handle_node_created)
    _bus.subscribe(NodeUpdated, handlers.handle_node_updated)
    _bus.subscribe(NodePublished, handlers.handle_node_published)
    _registered = True


def get_event_bus() -> EventBus:
    register_handlers()
    return _bus


__all__ = ["EventBus", "get_event_bus", "register_handlers"]

from __future__ import annotations

import logging
import time
from collections.abc import Mapping
from dataclasses import dataclass
from typing import Any

from domains.product.nodes.application.ports import Outbox
from packages.core import with_trace

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class NodeEvent:
    name: str
    payload: Mapping[str, Any]
    key: str | None = None
    context: Mapping[str, Any] | None = None


class NodeEventPublisher:
    """Thin facade over the outbox publisher with basic observability."""

    def __init__(self, outbox: Outbox | None) -> None:
        self._outbox = outbox

    @with_trace
    def publish(self, event: NodeEvent) -> None:
        if self._outbox is None:
            logger.debug("node_event_outbox_skipped", extra={"event": event.name})
            return
        started = time.perf_counter()
        try:
            self._outbox.publish(event.name, dict(event.payload), key=event.key)  # type: ignore[arg-type]
        except Exception as exc:  # pragma: no cover - best effort logging
            extra: dict[str, Any] = {"event": event.name}
            if event.context:
                extra.update(dict(event.context))
            logger.exception("node_event_outbox_failed", extra=extra, exc_info=exc)
            return
        duration_ms = (time.perf_counter() - started) * 1000
        logger.debug(
            "node_event_outbox_published",
            extra={
                "event": event.name,
                "duration_ms": round(duration_ms, 2),
                "key": event.key,
            },
        )


__all__ = ["NodeEvent", "NodeEventPublisher"]

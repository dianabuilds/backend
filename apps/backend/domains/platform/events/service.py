from __future__ import annotations

import logging
from dataclasses import dataclass

from domains.platform.events.ports import (
    EventBus,
    Handler,
    OutboxPublisher,
)
from domains.platform.telemetry.application.event_metrics_service import (
    event_metrics,
)

logger = logging.getLogger(__name__)


@dataclass
class Events:
    outbox: OutboxPublisher
    bus: EventBus

    # Publish integration event
    def publish(self, topic: str, payload: dict, key: str | None = None) -> None:
        # Record basic event counter
        try:
            event_metrics.inc(topic)
        except (RuntimeError, ValueError) as exc:
            logger.debug(
                "event_metrics_inc_failed", extra={"topic": topic}, exc_info=exc
            )
        self.outbox.publish(topic=topic, payload=payload, key=key)

    # Subscribe handler to topic
    def on(self, topic: str, handler: Handler) -> None:
        self.bus.subscribe(topic, handler)

    # Run delivery loop (for transports that need it)
    def run(self, block_ms: int | None = None, count: int | None = None) -> None:
        self.bus.run(block_ms=block_ms, count=count)


__all__ = ["Events"]

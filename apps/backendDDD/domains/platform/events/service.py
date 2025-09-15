from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from apps.backendDDD.domains.platform.telemetry.application.event_metrics_service import (
    event_metrics,
)

from apps.backendDDD.domains.platform.events.ports import (
    EventBus,
    Handler,
    OutboxPublisher,
)


@dataclass
class Events:
    outbox: OutboxPublisher
    bus: EventBus

    # Publish integration event
    def publish(self, topic: str, payload: dict, key: str | None = None) -> None:
        # Record basic event counter (tenant/user if available)
        tenant_or_user: str | None = None
        try:
            # Try common keys without coupling to specific domains
            for k in ("tenant_id", "author_id", "user_id", "id"):
                v: Any = payload.get(k)  # type: ignore[assignment]
                if v:
                    tenant_or_user = str(v)
                    break
        except Exception:
            tenant_or_user = None
        try:
            event_metrics.inc(topic, tenant_or_user)
        except Exception:
            pass
        self.outbox.publish(topic=topic, payload=payload, key=key)

    # Subscribe handler to topic
    def on(self, topic: str, handler: Handler) -> None:
        self.bus.subscribe(topic, handler)

    # Run delivery loop (for transports that need it)
    def run(self, block_ms: int | None = None, count: int | None = None) -> None:
        self.bus.run(block_ms=block_ms, count=count)


__all__ = ["Events"]

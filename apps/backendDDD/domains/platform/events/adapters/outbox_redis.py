from __future__ import annotations

from apps.backendDDD.packages.core.redis_outbox import RedisOutboxCore
from apps.backendDDD.packages.core.schema_registry import validate_event_payload


class RedisOutbox:
    def __init__(self, redis_url: str):
        self._core = RedisOutboxCore(redis_url)

    def publish(self, topic: str, payload: dict, key: str | None = None) -> None:
        # Validate against JSON schema if available
        try:
            validate_event_payload(topic, payload)
        except Exception:
            # Keep strict: raise to let caller handle/report
            raise
        self._core.publish(topic=topic, payload=payload, key=key)


__all__ = ["RedisOutbox"]

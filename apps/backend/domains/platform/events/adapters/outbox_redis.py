from __future__ import annotations

from typing import Any

from packages.core.redis_outbox import RedisOutboxCore
from packages.core.schema_registry import validate_event_payload


class RedisOutbox:
    def __init__(self, redis_url: str, redis_client: Any | None = None):
        self._core = RedisOutboxCore(redis_url, client=redis_client)

    def publish(self, topic: str, payload: dict, key: str | None = None) -> None:
        # Validate against JSON schema if available
        try:
            validate_event_payload(topic, payload)
        except (ValueError, TypeError) as exc:
            raise ValueError(f"invalid event payload for {topic}") from exc
        self._core.publish(topic=topic, payload=payload, key=key)


__all__ = ["RedisOutbox"]

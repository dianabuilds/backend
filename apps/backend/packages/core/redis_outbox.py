from __future__ import annotations

import json
from typing import Any

try:
    # redis-py provides asyncio and sync clients. We use sync for simplicity here.
    import redis  # type: ignore
except Exception:  # pragma: no cover - import guard
    redis = None  # type: ignore


class RedisOutboxCore:
    """Low-level Redis Streams outbox.

    Uses a stream per topic: key = f"events:{topic}". Writes entries with fields
    {"key": key, "payload": json, "ts": epoch_ms}.
    """

    def __init__(self, redis_url: str):
        if redis is None:  # pragma: no cover
            raise RuntimeError("redis-py is required for Redis outbox")
        self._r = redis.Redis.from_url(redis_url, decode_responses=True)

    def publish(self, topic: str, payload: dict, key: str | None = None) -> str:
        stream = f"events:{topic}"
        data: dict[str, Any] = {"payload": json.dumps(payload)}
        if key is not None:
            data["key"] = key
        # Simple retry with backoff for transient network hiccups
        delay = 0.05
        last_err: Exception | None = None
        for _ in range(5):
            try:
                msg_id = self._r.xadd(stream, data)
                return msg_id
            except Exception as e:  # pragma: no cover - network transient
                last_err = e
                import time as _t

                _t.sleep(delay)
                delay = min(delay * 2, 0.5)
        # Exhausted retries
        if last_err:
            raise last_err
        # Fallback should never reach here
        raise RuntimeError("failed to publish to redis outbox")


__all__ = ["RedisOutboxCore"]

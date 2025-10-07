from __future__ import annotations

import json
from importlib import import_module
from typing import Any, Protocol, cast

try:
    _redis_module = import_module("redis")
except ModuleNotFoundError as exc:  # pragma: no cover - optional dependency guard
    raise RuntimeError("redis package is required for Redis outbox") from exc

RedisFactory = _redis_module.Redis


class RedisStreamWriter(Protocol):
    """Subset of Redis Stream commands used by the outbox."""

    def xadd(self, name: str, fields: dict[str, Any]) -> str: ...


class RedisOutboxCore:
    """Low-level Redis Streams outbox."""

    def __init__(self, redis_url: str, client: RedisStreamWriter | None = None):
        if client is not None:
            self._client = client
        else:
            self._client = cast(
                RedisStreamWriter,
                RedisFactory.from_url(redis_url, decode_responses=True),
            )

    def publish(self, topic: str, payload: dict, key: str | None = None) -> str:
        stream = f"events:{topic}"
        data: dict[str, Any] = {"payload": json.dumps(payload)}
        if key is not None:
            data["key"] = key
        delay = 0.05
        last_err: Exception | None = None
        for _ in range(5):
            try:
                return self._client.xadd(stream, data)
            except Exception as exc:  # pragma: no cover - network transient
                last_err = exc
                import time as _time

                _time.sleep(delay)
                delay = min(delay * 2, 0.5)
        if last_err is not None:
            raise last_err
        raise RuntimeError("failed to publish to redis outbox")


__all__ = ["RedisOutboxCore"]

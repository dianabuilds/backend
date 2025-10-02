from __future__ import annotations

import hashlib
import json
from collections.abc import Mapping
from datetime import date, datetime
from decimal import Decimal
from typing import Any

import redis  # type: ignore


def _normalize(value: Any) -> Any:
    if isinstance(value, Mapping):
        return {
            str(k): _normalize(v) for k, v in sorted(value.items(), key=lambda item: str(item[0]))
        }
    if isinstance(value, (list, tuple)):
        return [_normalize(v) for v in value]
    if isinstance(value, set):
        normalized = [_normalize(v) for v in value]
        return sorted(
            normalized,
            key=lambda item: json.dumps(
                item,
                sort_keys=True,
                separators=(",", ":"),
                ensure_ascii=False,
                default=str,
            ),
        )
    if isinstance(value, Decimal):
        return float(value)
    if isinstance(value, (datetime, date)):
        return value.isoformat()
    if isinstance(value, bytes):
        return value.decode("utf-8", errors="replace")
    if isinstance(value, (str, int, float, bool)) or value is None:
        return value
    return str(value)


def _hash_payload(payload: Mapping[str, Any]) -> str:
    normalized = _normalize(dict(payload))
    data = json.dumps(normalized, sort_keys=True, separators=(",", ":"), ensure_ascii=False)
    return hashlib.sha256(data.encode("utf-8")).hexdigest()


class RedisIdempotency:
    def __init__(self, r: redis.Redis, ttl_seconds: int = 24 * 3600):
        self._r = r
        self._ttl = ttl_seconds

    def key(self, topic: str, entity_key: str | None, payload: Mapping[str, Any]) -> str:
        ph = _hash_payload(payload)
        ek = entity_key or "_"
        return f"idem:{topic}:{ek}:{ph}"

    def check_and_set(self, topic: str, entity_key: str | None, payload: Mapping[str, Any]) -> bool:
        k = self.key(topic, entity_key, payload)
        # Set if not exists with TTL
        return bool(self._r.set(k, "1", nx=True, ex=self._ttl))

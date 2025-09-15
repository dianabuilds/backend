from __future__ import annotations

import hashlib

import redis  # type: ignore


def _hash_payload(payload: dict) -> str:
    m = hashlib.sha256()
    m.update(repr(sorted(payload.items())).encode("utf-8"))
    return m.hexdigest()


class RedisIdempotency:
    def __init__(self, r: redis.Redis, ttl_seconds: int = 24 * 3600):
        self._r = r
        self._ttl = ttl_seconds

    def key(self, topic: str, entity_key: str | None, payload: dict) -> str:
        ph = _hash_payload(payload)
        ek = entity_key or "_"
        return f"idem:{topic}:{ek}:{ph}"

    def check_and_set(self, topic: str, entity_key: str | None, payload: dict) -> bool:
        k = self.key(topic, entity_key, payload)
        # Set if not exists with TTL
        return bool(self._r.set(k, "1", nx=True, ex=self._ttl))

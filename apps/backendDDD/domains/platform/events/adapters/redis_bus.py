from __future__ import annotations

import json
from typing import Any

import redis  # type: ignore


class RedisBus:
    """Thin adapter over Redis Streams for events.* topics.

    - Streams: events:<topic>
    - Consumer groups created on demand
    """

    def __init__(self, redis_url: str):
        self._r = redis.Redis.from_url(redis_url, decode_responses=True)

    def stream_key(self, topic: str) -> str:
        return f"events:{topic}"

    def ensure_group(self, topic: str, group: str) -> None:
        stream = self.stream_key(topic)
        try:
            self._r.xgroup_create(name=stream, groupname=group, id="0-0", mkstream=True)
        except Exception:
            # BUSYGROUP or exists
            pass

    def read_batch(
        self, topics: list[str], group: str, consumer: str, count: int, block_ms: int
    ) -> list[tuple[str, list[tuple[str, dict[str, str]]]]]:
        streams = {self.stream_key(t): ">" for t in topics}
        return (
            self._r.xreadgroup(group, consumer, streams, count=count, block=block_ms)
            or []
        )

    def ack(self, topic: str, group: str, msg_id: str) -> None:
        self._r.xack(self.stream_key(topic), group, msg_id)

    def xlen(self, topic: str) -> int:
        return int(self._r.xlen(self.stream_key(topic)))

    def xpending(self, topic: str, group: str) -> int:
        try:
            info = self._r.xpending(self.stream_key(topic), group)
            return (
                int(info.get("pending", 0)) if isinstance(info, dict) else int(info[0])
            )
        except Exception:
            return 0

    def to_payload(self, fields: dict[str, str]) -> dict[str, Any]:
        try:
            return json.loads(fields.get("payload", "{}"))
        except Exception:
            return {}

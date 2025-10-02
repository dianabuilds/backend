from __future__ import annotations

import json
import logging
from json import JSONDecodeError
from typing import Any

import redis  # type: ignore
from redis.exceptions import RedisError  # type: ignore[import]

logger = logging.getLogger(__name__)


class RedisBus:
    """Thin adapter over Redis Streams for events.* topics.

    - Streams: events:<topic>
    - Consumer groups created on demand
    """

    def __init__(self, redis_url: str, client: Any | None = None):
        self._r = client or redis.Redis.from_url(redis_url, decode_responses=True)

    def stream_key(self, topic: str) -> str:
        return f"events:{topic}"

    def ensure_group(self, topic: str, group: str) -> None:
        stream = self.stream_key(topic)
        try:
            self._r.xgroup_create(name=stream, groupname=group, id="0-0", mkstream=True)
        except RedisError as exc:
            message = str(exc)
            if (
                "BUSYGROUP" not in message
                and "ERR Consumer Group name already exists" not in message
            ):
                logger.warning(
                    "Failed to ensure consumer group for stream=%s group=%s: %s",
                    stream,
                    group,
                    exc,
                )

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
        except RedisError as exc:
            logger.debug(
                "Failed to fetch pending info for stream=%s group=%s: %s",
                self.stream_key(topic),
                group,
                exc,
            )
            return 0

    def to_payload(self, fields: dict[str, str]) -> dict[str, Any]:
        try:
            return json.loads(fields.get("payload", "{}"))
        except (JSONDecodeError, TypeError) as exc:
            logger.debug("Failed to decode payload for fields=%s: %s", fields, exc)
            return {}

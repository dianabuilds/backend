from __future__ import annotations

import json
import logging
from importlib import import_module
from json import JSONDecodeError
from typing import Any, Protocol, cast

logger = logging.getLogger(__name__)

try:
    _redis_module = import_module("redis")
    _redis_exceptions = import_module("redis.exceptions")
except ModuleNotFoundError as exc:  # pragma: no cover - optional dependency guard
    raise RuntimeError("redis package is required for RedisBus") from exc

RedisError = cast(type[Exception], getattr(_redis_exceptions, "RedisError", Exception))
RedisFactory = _redis_module.Redis


class RedisStreamsClient(Protocol):
    """Protocol describing the subset of Redis stream commands we rely on."""

    def xgroup_create(
        self, name: str, groupname: str, id: str, mkstream: bool = False  # noqa: A002
    ) -> Any:
        del name, groupname, id, mkstream
        raise NotImplementedError

    def xreadgroup(
        self,
        groupname: str,
        consumername: str,
        streams: dict[str, str],
        *,
        count: int | None = None,
        block: int | None = None,
    ) -> list[tuple[str, list[tuple[str, dict[str, str]]]]]:
        del groupname, consumername, streams, count, block
        raise NotImplementedError

    def xack(self, name: str, groupname: str, *ids: str) -> Any:
        del name, groupname, ids
        raise NotImplementedError

    def xlen(self, name: str) -> int:
        del name
        raise NotImplementedError

    def xpending(self, name: str, groupname: str) -> Any:
        del name, groupname
        raise NotImplementedError


class RedisBus:
    """Thin adapter over Redis Streams for events.* topics."""

    def __init__(self, redis_url: str, client: RedisStreamsClient | None = None):
        if client is not None:
            self._client = client
        else:
            self._client = cast(
                RedisStreamsClient,
                RedisFactory.from_url(redis_url, decode_responses=True),
            )

    @staticmethod
    def stream_key(topic: str) -> str:
        return f"events:{topic}"

    def ensure_group(self, topic: str, group: str) -> None:
        stream = self.stream_key(topic)
        try:
            self._client.xgroup_create(
                name=stream, groupname=group, id="0-0", mkstream=True
            )
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
        streams = {self.stream_key(topic): ">" for topic in topics}
        return (
            self._client.xreadgroup(
                group,
                consumer,
                streams,
                count=count,
                block=block_ms,
            )
            or []
        )

    def ack(self, topic: str, group: str, msg_id: str) -> None:
        self._client.xack(self.stream_key(topic), group, msg_id)

    def xlen(self, topic: str) -> int:
        return int(self._client.xlen(self.stream_key(topic)))

    def xpending(self, topic: str, group: str) -> int:
        try:
            info = self._client.xpending(self.stream_key(topic), group)
            if isinstance(info, dict):
                return int(info.get("pending", 0))
            if isinstance(info, (list, tuple)) and info:
                return int(info[0])
            return int(info)
        except (RedisError, ValueError, TypeError) as exc:
            logger.debug(
                "Failed to fetch pending info for stream=%s group=%s: %s",
                self.stream_key(topic),
                group,
                exc,
            )
            return 0

    @staticmethod
    def to_payload(fields: dict[str, str]) -> dict[str, Any]:
        try:
            raw = json.loads(fields.get("payload", "{}"))
        except (JSONDecodeError, TypeError) as exc:
            logger.debug("Failed to decode payload for fields=%s: %s", fields, exc)
            return {}
        if isinstance(raw, dict):
            return {str(key): value for key, value in raw.items()}
        return {"value": raw}


__all__ = ["RedisBus"]

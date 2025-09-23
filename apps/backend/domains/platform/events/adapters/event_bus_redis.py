from __future__ import annotations

from typing import Any

from domains.platform.events.logic.relay import RedisRelay
from domains.platform.events.ports import EventBus, Handler


class RedisEventBus(EventBus):
    def __init__(
        self,
        redis_url: str,
        topics: list[str],
        group: str = "relay",
        consumer: str | None = None,
        redis_client: Any | None = None,
    ):
        self._relay = RedisRelay(
            redis_url=redis_url,
            topics=topics,
            group=group,
            consumer=consumer,
            redis_client=redis_client,
        )
        self._routes: dict[str, Handler] = {}

    def subscribe(self, topic: str, handler: Handler) -> None:
        self._routes[topic] = handler

    def run(self, block_ms: int | None = None, count: int | None = None) -> None:
        self._relay.loop(routes=self._routes, block_ms=block_ms, count=count)


__all__ = ["RedisEventBus"]

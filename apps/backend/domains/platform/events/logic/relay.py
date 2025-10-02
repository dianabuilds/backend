from __future__ import annotations

import os
import time
from collections.abc import Callable
from typing import Any

import redis  # type: ignore

from domains.platform.events.adapters.redis_bus import RedisBus
from domains.platform.events.logic.idempotency import RedisIdempotency
from domains.platform.events.logic.policies import rate_limit
from domains.platform.telemetry.application.event_metrics_service import (
    event_metrics,
)
from packages.core.schema_registry import validate_event_payload

Handler = Callable[[str, dict], None]


class RedisRelay:
    """Platform events relay with idempotency, basic rate-limit and DLQ.

    Env:
      REDIS_URL, EVENT_TOPICS (comma list), EVENT_GROUP, EVENT_CONSUMER,
      EVENT_BLOCK_MS, EVENT_COUNT, EVENT_IDEMPOTENCY_TTL, EVENT_RATE_QPS
    """

    def __init__(
        self,
        redis_url: str,
        topics: list[str],
        group: str = "relay",
        consumer: str | None = None,
        redis_client: Any | None = None,
    ):
        self._r = redis_client or redis.Redis.from_url(redis_url, decode_responses=True)
        self._bus = RedisBus(redis_url, client=self._r)
        self._group = group
        self._consumer = consumer or f"c-{os.getpid()}"
        self._topics = topics
        self._stopped = False
        self._idem = RedisIdempotency(
            self._r, ttl_seconds=int(os.getenv("EVENT_IDEMPOTENCY_TTL", "86400"))
        )
        self._rate_qps = int(os.getenv("EVENT_RATE_QPS", "1000"))
        for t in topics:
            self._bus.ensure_group(t, self._group)

    def loop(
        self,
        routes: dict[str, Handler],
        block_ms: int | None = None,
        count: int | None = None,
    ) -> None:
        block = int(os.getenv("EVENT_BLOCK_MS", str(block_ms or 5000)))
        batch = int(os.getenv("EVENT_COUNT", str(count or 100)))
        while not self._stopped:
            try:
                resp = self._bus.read_batch(self._topics, self._group, self._consumer, batch, block)
            except Exception:
                if self._stopped:
                    break
                time.sleep(1.0)
                continue
            if not resp:
                continue
            for stream, messages in resp:
                topic = stream.split(":", 1)[1]
                for msg_id, fields in messages:
                    payload = self._bus.to_payload(fields)
                    entity_key = fields.get("key")
                    # rate limit per topic
                    if not rate_limit(
                        self._r, key=f"rate:{topic}", limit=self._rate_qps, window_sec=1
                    ):
                        # skip ack to reprocess later
                        continue
                    # idempotency
                    if not self._idem.check_and_set(topic, entity_key, payload):
                        self._bus.ack(topic, self._group, msg_id)
                        continue
                    try:
                        # Validate event payload if schema exists
                        try:
                            validate_event_payload(topic, payload)
                        except Exception:
                            # invalid payload -> DLQ
                            raise
                        handler = routes.get(topic)
                        if handler:
                            import time as _t

                            t0 = _t.perf_counter()
                            ok = True
                            try:
                                handler(topic, payload)
                            except Exception:
                                ok = False
                                raise
                            finally:
                                try:
                                    dt = (_t.perf_counter() - t0) * 1000.0
                                    event_metrics.record_handler(
                                        topic,
                                        getattr(handler, "__name__", "handler"),
                                        ok,
                                        dt,
                                    )
                                except Exception:
                                    pass
                        self._bus.ack(topic, self._group, msg_id)
                    except Exception:
                        # push to DLQ stream and ack original to avoid hot-loop
                        try:
                            self._r.xadd(
                                f"events:dlq:{topic}",
                                {
                                    "payload": fields.get("payload", "{}"),
                                    "key": entity_key or "_",
                                },
                            )
                        finally:
                            self._bus.ack(topic, self._group, msg_id)

    def stop(self) -> None:
        self._stopped = True
        try:
            self._r.close()
        except Exception:
            pass

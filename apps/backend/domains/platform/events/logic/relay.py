from __future__ import annotations

import logging
import os
import time
from collections.abc import Callable
from typing import Any

import redis  # type: ignore
from redis.exceptions import RedisError  # type: ignore[import]

from domains.platform.events.adapters.redis_bus import RedisBus
from domains.platform.events.logic.idempotency import RedisIdempotency
from domains.platform.events.logic.policies import rate_limit
from domains.platform.telemetry.application.event_metrics_service import (
    event_metrics,
)
from packages.core.schema_registry import validate_event_payload

Handler = Callable[[str, dict], None]


logger = logging.getLogger(__name__)


class RedisRelay:
    """Platform events relay with idempotency, rate-limits, metrics, and DLQ.

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
        for topic in topics:
            self._bus.ensure_group(topic, self._group)

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
                resp = self._bus.read_batch(
                    self._topics, self._group, self._consumer, batch, block
                )
            except RedisError as exc:
                if self._stopped:
                    break
                logger.warning("Failed to read events from Redis: %s", exc)
                time.sleep(1.0)
                continue
            if not resp:
                continue
            for stream, messages in resp:
                topic = stream.split(":", 1)[1] if ":" in stream else stream
                for msg_id, fields in messages:
                    try:
                        self._process_message(topic, msg_id, fields, routes)
                    except Exception as exc:  # pragma: no cover - defensive fallback
                        self._handle_failure(topic, msg_id, fields, exc)

    def stop(self) -> None:
        self._stopped = True
        try:
            self._r.close()
        except RedisError as exc:
            logger.debug("Failed to close Redis client cleanly: %s", exc)

    def _process_message(
        self,
        topic: str,
        msg_id: str,
        fields: dict[str, str],
        routes: dict[str, Handler],
    ) -> None:
        payload = self._bus.to_payload(fields)
        entity_key = fields.get("key")
        if not rate_limit(
            self._r,
            key=f"rate:{topic}",
            limit=self._rate_qps,
            window_sec=1,
        ):
            # Skip ack so the message is retried later.
            return
        if not self._idem.check_and_set(topic, entity_key, payload):
            self._ack(topic, msg_id)
            return
        try:
            validate_event_payload(topic, payload)
        except (ValueError, TypeError) as exc:
            raise ValueError(f"Invalid payload for topic '{topic}'") from exc
        handler = routes.get(topic)
        if handler:
            ok = True
            started_at = time.perf_counter()
            try:
                handler(topic, payload)
            except Exception:
                ok = False
                raise
            finally:
                try:
                    elapsed_ms = max((time.perf_counter() - started_at) * 1000.0, 0.0)
                    event_metrics.record_handler(
                        topic,
                        getattr(handler, "__name__", "handler"),
                        ok,
                        elapsed_ms,
                    )
                except (RuntimeError, ValueError) as exc:
                    logger.debug(
                        "Failed to record handler metrics for topic %s: %s",
                        topic,
                        exc,
                    )
        self._ack(topic, msg_id)

    def _handle_failure(
        self,
        topic: str,
        msg_id: str,
        fields: dict[str, str],
        error: Exception,
    ) -> None:
        entity_key = fields.get("key") or "_"
        payload_raw = fields.get("payload", "{}")
        logger.exception(
            "Failed to process event topic=%s key=%s id=%s",
            topic,
            entity_key,
            msg_id,
            exc_info=error,
        )
        dlq_key = f"events:dlq:{topic}"
        try:
            self._r.xadd(
                dlq_key,
                {
                    "payload": payload_raw,
                    "key": entity_key,
                },
            )
        except RedisError as dlq_exc:
            logger.error(
                "Failed to push event to DLQ topic=%s key=%s id=%s: %s",
                topic,
                entity_key,
                msg_id,
                dlq_exc,
            )
        finally:
            self._ack(topic, msg_id)

    def _ack(self, topic: str, msg_id: str) -> None:
        try:
            self._bus.ack(topic, self._group, msg_id)
        except RedisError as exc:
            logger.warning("Failed to ACK event topic=%s id=%s: %s", topic, msg_id, exc)

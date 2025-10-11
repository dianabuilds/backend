from __future__ import annotations

import builtins
import hashlib
import json
import logging
import math
import time
from collections.abc import Iterable
from dataclasses import dataclass
from typing import Any
from urllib.parse import urlparse

import redis.asyncio as redis  # type: ignore

from domains.platform.telemetry.ports.rum_port import IRumRepository

_DEFAULT_KEY_PREFIX = "telemetry:rum"
_STATE_TTL_SECONDS = 72 * 3600
_ERROR_TTL_SECONDS = 30 * 24 * 3600

logger = logging.getLogger(__name__)


@dataclass(slots=True)
class RumAggregate:
    key: str
    event: str
    category: str
    route: str
    bucket_ms: int
    count: int
    sums: dict[str, float]
    sum_squares: dict[str, float]
    last_ts: int

    def average(self, metric: str) -> float | None:
        total = self.sums.get(metric)
        if total is None or self.count <= 0:
            return None
        return total / float(self.count)


def _now_ms() -> int:
    return int(time.time() * 1000)


def _coerce_ts(value: Any, *, fallback: int | None = None) -> int:
    if isinstance(value, int):
        return value
    if isinstance(value, float) and math.isfinite(value):
        return int(value)
    return fallback if fallback is not None else _now_ms()


def _to_int(value: Any, default: int = 0) -> int:
    try:
        if isinstance(value, (int, float)):
            return int(value)
        return int(float(str(value)))
    except (TypeError, ValueError):
        return default


def _to_float(value: Any, default: float = 0.0) -> float:
    try:
        if isinstance(value, (int, float)):
            return float(value)
        return float(str(value))
    except (TypeError, ValueError):
        return default


def _normalise_route(url: str | None) -> str:
    if not url:
        return "unknown"
    parsed = urlparse(url)
    netloc = (parsed.netloc or "").lower()
    path = parsed.path or "/"
    route = f"{netloc}{path}" if netloc else path
    route = route.strip() or "unknown"
    return route[:256]


def _hash_route(route: str) -> str:
    return hashlib.sha1(route.encode("utf-8"), usedforsecurity=False).hexdigest()[:12]


def _iter_numeric_metrics(data: Any) -> Iterable[tuple[str, float]]:
    if not isinstance(data, dict):
        return
    for key, value in data.items():
        if isinstance(value, (int, float)) and math.isfinite(value):
            yield str(key), float(value)


class RumRedisRepository(IRumRepository):
    def __init__(
        self,
        client: redis.Redis,
        *,
        key_prefix: str = _DEFAULT_KEY_PREFIX,
        state_ttl_seconds: int = _STATE_TTL_SECONDS,
        error_ttl_seconds: int = _ERROR_TTL_SECONDS,
    ) -> None:
        self._redis = client
        self._state_key = f"{key_prefix}:state:raw"
        self._error_key = f"{key_prefix}:error:raw"
        self._agg_prefix = f"{key_prefix}:agg"
        self._agg_pending_key = f"{key_prefix}:agg:pending"
        self._state_ttl = max(int(state_ttl_seconds), 60)
        self._error_ttl = max(int(error_ttl_seconds), self._state_ttl)

    async def add(self, event: dict[str, Any]) -> None:
        payload = dict(event or {})
        now_ms = _now_ms()
        ts_ms = _coerce_ts(payload.get("ts"), fallback=now_ms)
        payload["ts"] = ts_ms

        event_name = str(payload.get("event") or "unknown").strip() or "unknown"
        url = str(payload.get("url") or "").strip()
        route = _normalise_route(url)
        category = self._classify_event(event_name)

        serialized = json.dumps(
            {**payload, "event": event_name, "url": url}, ensure_ascii=False
        )

        raw_key, ttl = self._raw_key_and_ttl(category)
        cutoff_ms = now_ms - (ttl * 1000)

        pipe = self._redis.pipeline()
        pipe.zadd(raw_key, {serialized: float(ts_ms)})
        pipe.zremrangebyscore(raw_key, 0, cutoff_ms)
        pipe.expire(raw_key, ttl)

        bucket_ms = (ts_ms // 60000) * 60000
        agg_key = self._agg_key(category, event_name, bucket_ms, route)
        metrics = list(_iter_numeric_metrics(payload.get("data")))
        pipe.hincrby(agg_key, "count", 1)
        pipe.hset(
            agg_key,
            mapping={
                "event": event_name,
                "category": category,
                "route": route,
                "bucket_ms": bucket_ms,
                "last_ts": ts_ms,
            },
        )
        for metric_name, metric_value in metrics:
            pipe.hincrbyfloat(agg_key, f"sum:{metric_name}", metric_value)
            pipe.hincrbyfloat(
                agg_key, f"sumsq:{metric_name}", metric_value * metric_value
            )
        pipe.expire(agg_key, ttl)

        pipe.zadd(self._agg_pending_key, {agg_key: float(bucket_ms)})
        pipe.zremrangebyscore(
            self._agg_pending_key,
            0,
            now_ms - (self._error_ttl * 1000),
        )
        pipe.expire(self._agg_pending_key, self._error_ttl)

        await pipe.execute()

    async def list(self, limit: int) -> builtins.list[dict[str, Any]]:
        lim = max(int(limit), 0)
        if lim == 0:
            return []
        fetch = min(lim * 3 or 1, 3000)
        raw_errors = await self._redis.zrevrange(self._error_key, 0, fetch - 1)
        raw_states = await self._redis.zrevrange(self._state_key, 0, fetch - 1)

        events: list[dict[str, Any]] = []
        for raw in (*raw_states, *raw_errors):
            try:
                decoded = (
                    raw.decode("utf-8") if isinstance(raw, (bytes, bytearray)) else raw
                )
                obj = json.loads(decoded)
                obj["ts"] = _coerce_ts(obj.get("ts"))
            except Exception as exc:
                logger.debug("rum repository: failed to parse event payload: %s", exc)
                continue
            events.append(obj)

        events.sort(key=lambda item: item.get("ts") or 0, reverse=True)
        return events[:lim]

    async def fetch_pending_aggregates(
        self,
        ready_before_ms: int,
        *,
        limit: int = 100,
    ) -> builtins.list[RumAggregate]:
        upper = max(int(ready_before_ms), 0)
        keys = await self._redis.zrangebyscore(
            self._agg_pending_key,
            0,
            upper,
            start=0,
            num=max(int(limit), 0) or 0,
        )
        if not keys:
            return []
        pipe = self._redis.pipeline()
        for key in keys:
            pipe.hgetall(key)
        rows = await pipe.execute()

        aggregates: list[RumAggregate] = []
        stale: list[str] = []
        for key, raw in zip(keys, rows, strict=False):
            if not raw:
                stale.append(key)
                continue
            aggregates.append(self._parse_aggregate(key, raw))
        if stale:
            await self.ack_aggregates(stale)
        return aggregates

    async def ack_aggregates(self, keys: Iterable[str]) -> None:
        items = tuple(keys)
        if not items:
            return
        await self._redis.zrem(self._agg_pending_key, *items)

    def _parse_aggregate(self, key: str, raw: dict[str, Any]) -> RumAggregate:
        event = str(raw.get("event") or "unknown")
        category = str(raw.get("category") or "state")
        route = str(raw.get("route") or "unknown")
        bucket_ms = _coerce_ts(raw.get("bucket_ms"), fallback=0)
        last_ts = _coerce_ts(raw.get("last_ts"), fallback=bucket_ms)
        count = _to_int(raw.get("count"), default=0)
        sums: dict[str, float] = {}
        sum_squares: dict[str, float] = {}
        for field, value in raw.items():
            if field.startswith("sum:"):
                sums[field[4:]] = _to_float(value)
            elif field.startswith("sumsq:"):
                sum_squares[field[6:]] = _to_float(value)
        return RumAggregate(
            key=key,
            event=event,
            category=category,
            route=route,
            bucket_ms=bucket_ms,
            count=count,
            sums=sums,
            sum_squares=sum_squares,
            last_ts=last_ts,
        )

    def _classify_event(self, event_name: str) -> str:
        name = event_name.lower()
        if name.startswith("ui_") or name.endswith("_error") or "error" in name:
            return "error"
        return "state"

    def _raw_key_and_ttl(self, category: str) -> tuple[str, int]:
        if category == "error":
            return self._error_key, self._error_ttl
        return self._state_key, self._state_ttl

    def _agg_key(
        self, category: str, event_name: str, bucket_ms: int, route: str
    ) -> str:
        route_hash = _hash_route(route)
        safe_event = event_name.replace(":", "_").replace(" ", "_").lower()
        return f"{self._agg_prefix}:{category}:{safe_event}:{bucket_ms}:{route_hash}"


__all__ = ["RumRedisRepository", "RumAggregate"]

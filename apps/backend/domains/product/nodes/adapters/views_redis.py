from __future__ import annotations

from datetime import UTC, datetime, timedelta
from typing import Any

try:  # pragma: no cover - optional dependency
    import redis.asyncio as aioredis  # type: ignore[import-untyped]
except ImportError:  # pragma: no cover - optional dependency
    aioredis = None  # type: ignore[assignment]

from domains.product.nodes.application.ports import NodeViewsLimiter


def _seconds_until(dt: datetime, *, end: datetime) -> int:
    delta = end - dt
    return max(1, int(delta.total_seconds()))


class RedisNodeViewLimiter(NodeViewsLimiter):
    def __init__(
        self,
        client: Any,
        *,
        ttl_seconds: int | None = None,
        per_day: bool = True,
        prefix: str = "node:view",
    ) -> None:
        if aioredis is None:
            raise RuntimeError("redis_asyncio_required")
        self.client = client
        self.ttl_seconds = ttl_seconds
        self.per_day = per_day
        self.prefix = prefix.rstrip(":")

    async def should_count(
        self,
        node_id: int,
        *,
        viewer_id: str | None,
        fingerprint: str | None,
        at: datetime,
    ) -> bool:
        identifier = (viewer_id or "").strip()
        if not identifier:
            identifier = (fingerprint or "").strip()
        if not identifier:
            return True
        ts = at.astimezone(UTC)
        key_parts = [self.prefix, str(node_id), identifier]
        if self.per_day:
            key_parts.append(ts.date().isoformat())
        key = ":".join(key_parts)
        ttl = self.ttl_seconds
        if self.per_day:
            end_of_day = datetime.combine(
                ts.date() + timedelta(days=1), datetime.min.time(), tzinfo=UTC
            )
            ttl = _seconds_until(ts, end=end_of_day)
        elif ttl is None:
            ttl = 3600
        try:
            stored = await self.client.set(
                name=key, value=str(ts.timestamp()), ex=int(ttl), nx=True
            )
            return bool(stored)
        except Exception:  # pragma: no cover - best effort
            # Do not block view counting if Redis misbehaves
            return True


__all__ = ["RedisNodeViewLimiter"]

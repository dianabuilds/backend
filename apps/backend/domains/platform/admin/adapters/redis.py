from __future__ import annotations

import time
from dataclasses import dataclass
from datetime import UTC, datetime
from typing import Any

try:
    import redis.asyncio as aioredis  # type: ignore
    from redis.exceptions import RedisError  # type: ignore[import]
except Exception:  # pragma: no cover - optional dependency
    aioredis = None
    RedisError = Exception  # type: ignore


@dataclass
class RedisProbe:
    redis_url: str | None

    async def ping(self) -> dict[str, Any]:
        signal: dict[str, Any] = {
            "id": "redis:cache",
            "label": "Redis",
            "status": "unknown",
            "ok": None,
            "latency_ms": None,
            "last_heartbeat": None,
            "hint": None,
            "error": None,
        }
        if not self.redis_url:
            signal["hint"] = "Redis URL is not configured"
            return signal
        if aioredis is None:
            signal.update(
                {
                    "hint": "redis package unavailable, unable to ping cache",
                }
            )
            return signal

        client = aioredis.from_url(str(self.redis_url))
        start = time.perf_counter()
        try:
            await client.ping()
            latency_ms = (time.perf_counter() - start) * 1000.0
            now = datetime.now(UTC)
            signal.update(
                {
                    "status": "healthy",
                    "ok": True,
                    "latency_ms": round(latency_ms, 2),
                    "last_heartbeat": now,
                }
            )
        except RedisError as exc:
            signal.update(
                {
                    "status": "critical",
                    "ok": False,
                    "hint": f"Redis ping failed: {exc}",
                    "error": str(exc),
                    "last_heartbeat": datetime.now(UTC),
                }
            )
        finally:
            try:
                await client.close()
            except Exception:  # pragma: no cover - defensive
                pass
        return signal


__all__ = ["RedisProbe"]

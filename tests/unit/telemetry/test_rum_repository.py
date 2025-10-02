import time

import fakeredis.aioredis
import pytest

from domains.platform.telemetry.adapters.rum_repository import RumRedisRepository


@pytest.mark.asyncio
async def test_rum_redis_repository_categorizes_events() -> None:
    fake = fakeredis.aioredis.FakeRedis(decode_responses=True)
    repo = RumRedisRepository(fake, state_ttl_seconds=3600, error_ttl_seconds=86400)

    now_ms = int(time.time() * 1000)
    state_ts = now_ms - 2 * 60_000
    error_ts = now_ms - 30_000

    await repo.add(
        {
            "event": "navigation",
            "ts": state_ts,
            "url": "https://app.local/dashboard",
            "data": {"ttfb": 120.0, "domContentLoaded": 450.0},
        }
    )
    await repo.add(
        {
            "event": "ui_error",
            "ts": error_ts,
            "url": "https://app.local/dashboard",
            "data": {"message": "boom"},
        }
    )

    events = await repo.list(10)
    assert len(events) == 2
    assert events[0]["event"] == "ui_error"
    assert events[1]["event"] == "navigation"

    aggregates = await repo.fetch_pending_aggregates(ready_before_ms=_now_ms())
    assert aggregates, "expected pending aggregates"
    agg = next(a for a in aggregates if a.category == "state")
    assert agg.count == 1
    assert pytest.approx(agg.sums["ttfb"], rel=1e-6) == 120.0
    assert agg.average("ttfb") == pytest.approx(120.0)

    # cleanup pending keys to avoid leaking between tests
    await repo.ack_aggregates([a.key for a in aggregates])


@pytest.mark.asyncio
async def test_rum_redis_repository_fetch_pending_prunes_missing() -> None:
    fake = fakeredis.aioredis.FakeRedis(decode_responses=True)
    repo = RumRedisRepository(fake)

    now_ms = int(time.time() * 1000) - 3 * 60_000
    await repo.add(
        {"event": "navigation", "ts": now_ms, "url": "/", "data": {"ttfb": 50}}
    )

    aggregates = await repo.fetch_pending_aggregates(ready_before_ms=_now_ms())
    assert aggregates

    # Remove the underlying hash manually to emulate expiry
    await fake.delete(aggregates[0].key)
    stale = await repo.fetch_pending_aggregates(ready_before_ms=_now_ms())
    assert not stale


def _now_ms() -> int:
    return int(time.time() * 1000)

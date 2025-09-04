import logging

import fakeredis.aioredis
import pytest

from app.domains.telemetry.application.rum_service import RumMetricsService
from app.domains.telemetry.infrastructure.repositories.rum_repository import (
    RumRedisRepository,
)


@pytest.mark.asyncio
async def test_rum_service_summary() -> None:
    redis = fakeredis.aioredis.FakeRedis(decode_responses=True)
    repo = RumRedisRepository(redis, key="test:rum")
    service = RumMetricsService(repo)

    await service.record(
        {
            "event": "login_attempt",
            "ts": 1,
            "url": "https://example.com/login",
            "data": {"dur_ms": 120},
        }
    )
    await service.record(
        {
            "event": "navigation",
            "ts": 2,
            "url": "https://example.com/",
            "data": {"ttfb": 20, "domContentLoaded": 30, "loadEvent": 40},
        }
    )

    events = await service.list_events(10)
    assert events[0]["event"] == "navigation"
    assert events[1]["event"] == "login_attempt"

    summary = await service.summary(10)
    assert summary["counts"]["login_attempt"] == 1
    assert summary["navigation_avg"]["ttfb_ms"] == 20.0


@pytest.mark.asyncio
async def test_rum_service_invalid_payload(caplog: pytest.LogCaptureFixture) -> None:
    redis = fakeredis.aioredis.FakeRedis(decode_responses=True)
    repo = RumRedisRepository(redis, key="test:rum")
    service = RumMetricsService(repo)

    with caplog.at_level(logging.WARNING):
        await service.record({"event": 123, "url": "https://example.com"})

    events = await service.list_events(10)
    assert events == []
    assert "invalid RUM event payload" in caplog.text

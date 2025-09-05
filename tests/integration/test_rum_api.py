from __future__ import annotations

import types
import uuid

import fakeredis.aioredis
import pytest
from fastapi import FastAPI
from httpx import ASGITransport, AsyncClient

from app.api import rum_metrics
from app.api.deps import admin_required
from app.domains.telemetry.application.rum_service import RumMetricsService
from app.domains.telemetry.infrastructure.repositories.rum_repository import (
    RumRedisRepository,
)


@pytest.mark.asyncio
async def test_rum_events_filter_and_pagination() -> None:
    app = FastAPI()
    admin = types.SimpleNamespace(id=uuid.uuid4(), role="admin")
    app.dependency_overrides[admin_required] = lambda: admin

    redis = fakeredis.aioredis.FakeRedis(decode_responses=True)
    rum_metrics.rum_service = RumMetricsService(RumRedisRepository(redis, key="test:rum"))
    app.include_router(rum_metrics.admin_router)

    events = [
        {"event": "login", "ts": 1, "url": "https://a"},
        {"event": "navigation", "ts": 2, "url": "https://b"},
        {"event": "login", "ts": 3, "url": "https://b"},
        {"event": "login", "ts": 4, "url": "https://a"},
    ]
    for ev in events:
        await rum_metrics.rum_service.record(ev)

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        resp = await client.get("/admin/telemetry/rum", params={"event": "login", "url": "a"})
        assert resp.status_code == 200
        data = resp.json()
        assert [e["ts"] for e in data] == [4, 1]

        resp = await client.get(
            "/admin/telemetry/rum", params={"event": "login", "offset": 1, "limit": 1}
        )
        assert resp.status_code == 200
        data = resp.json()
        assert len(data) == 1
        assert data[0]["ts"] == 3

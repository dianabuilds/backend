from __future__ import annotations

import pytest
from fastapi import FastAPI
from httpx import ASGITransport, AsyncClient

from app.core.metrics import (
    _fallback_used_counts,
    _no_route_counts,
    _transition_counts,
    _transition_lock,
    metrics_storage,
    record_fallback_used,
    record_no_route,
    record_route_length,
)
from app.domains.telemetry.api import admin_metrics_router


@pytest.mark.asyncio
async def test_metrics_reliability():
    app = FastAPI()
    app.include_router(admin_metrics_router.router)

    dep = None
    for route in admin_metrics_router.router.routes:
        if route.path == "/admin/metrics/reliability":
            dep = route.dependant.dependencies[0].call
            break
    assert dep
    app.dependency_overrides[dep] = lambda: None

    metrics_storage.reset()
    with _transition_lock:
        _transition_counts.clear()
        _no_route_counts.clear()
        _fallback_used_counts.clear()

    metrics_storage.record(100, 200, "GET", "/x", "ws1")
    metrics_storage.record(120, 404, "GET", "/x", "ws1")
    metrics_storage.record(150, 500, "GET", "/x", "ws1")

    record_route_length(1, "ws1")
    record_no_route("ws1")
    record_fallback_used("ws1")

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        resp = await client.get(
            "/admin/metrics/reliability", params={"workspace": "ws1"}
        )
    assert resp.status_code == 200
    data = resp.json()
    assert data["count_4xx"] == 1
    assert data["count_5xx"] == 1
    assert data["p95"] == 150
    assert data["no_route_percent"] == 50.0
    assert data["fallback_percent"] == 50.0
    assert data["rps"] == pytest.approx(3 / 3600)

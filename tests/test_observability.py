import json
import pytest


@pytest.mark.asyncio
async def test_health_and_ready(client):
    r = await client.get("/healthz")
    assert r.status_code == 200
    r = await client.get("/readyz")
    assert r.status_code == 200
    data = r.json()
    assert data["db"] == "ok"


@pytest.mark.asyncio
async def test_metrics_endpoint(client):
    # trigger a request to have at least one metric
    await client.get("/healthz")
    r = await client.get("/metrics")
    assert r.status_code == 200
    body = r.text
    assert "http_requests_total" in body
    assert "http_request_duration_ms_bucket" in body

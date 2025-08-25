"""CORS headers are correctly handled."""

import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_cors_preflight_and_requests(client: AsyncClient):
    origin = "https://example.com"
    headers = {
        "Origin": origin,
        "Access-Control-Request-Method": "GET",
        "Access-Control-Request-Headers": "Content-Type",
    }

    # Preflight request
    response = await client.options("/", headers=headers)
    assert response.status_code == 200
    assert response.headers["access-control-allow-origin"] == origin
    assert response.headers["access-control-allow-credentials"] == "true"
    assert "GET" in response.headers["access-control-allow-methods"]
    assert "Content-Type" in response.headers["access-control-allow-headers"]
    assert response.headers["access-control-max-age"] == "600"
    vary = {h.strip() for h in response.headers["vary"].split(",")}
    assert "Origin" in vary

    # Simple request with allowed origin
    response = await client.get("/", headers={"Origin": origin})
    assert response.status_code == 200
    assert response.headers["access-control-allow-origin"] == origin
    assert response.headers["access-control-allow-credentials"] == "true"
    vary = {h.strip() for h in response.headers["vary"].split(",")}
    assert "Origin" in vary

    # Request with disallowed origin
    bad_origin = "https://evil.com"
    response = await client.get("/", headers={"Origin": bad_origin})
    assert response.status_code == 200
    assert "access-control-allow-origin" not in response.headers

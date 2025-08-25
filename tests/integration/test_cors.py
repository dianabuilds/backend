"""CORS headers are correctly handled."""

import pytest
from fastapi import Response
from httpx import AsyncClient

from app.main import app


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


@app.get("/cors-cookie")
def cors_cookie() -> Response:
    response = Response(content="", media_type="text/plain")
    response.set_cookie("sessionid", "1")
    return response


@pytest.mark.asyncio
async def test_cors_allows_credentials(client: AsyncClient) -> None:
    origin = "http://client.example"
    response = await client.get("/cors-cookie", headers={"Origin": origin})
    assert response.status_code == 200
    assert response.headers.get("access-control-allow-origin") == origin
    assert response.headers.get("access-control-allow-credentials") == "true"
    assert "set-cookie" in response.headers


@pytest.mark.asyncio
async def test_cors_preflight_allows_custom_header(client: AsyncClient) -> None:
    origin = "http://client.example"
    response = await client.options(
        "/auth/login",
        headers={
            "Origin": origin,
            "Access-Control-Request-Method": "POST",
            "Access-Control-Request-Headers": "X-Custom-Header",
        },
        follow_redirects=False,
    )
    assert response.status_code == 200
    allow_headers = response.headers.get("access-control-allow-headers", "").lower()
    assert "x-custom-header" in allow_headers
    allow_methods = response.headers.get("access-control-allow-methods", "").lower()
    assert "post" in allow_methods
    assert response.headers.get("access-control-allow-origin") == origin


@pytest.mark.asyncio
async def test_options_no_redirect(client: AsyncClient) -> None:
    origin = "http://client.example"
    response = await client.options(
        "/auth/login",
        headers={
            "Origin": origin,
            "Access-Control-Request-Method": "POST",
        },
        follow_redirects=False,
    )
    assert response.status_code == 200
    assert not 300 <= response.status_code < 400


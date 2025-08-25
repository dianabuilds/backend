import pytest
from httpx import AsyncClient
from fastapi import Response

from app.main import app


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

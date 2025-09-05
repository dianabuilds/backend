from __future__ import annotations

import importlib
import sys

import httpx
import pytest

app_module = importlib.import_module("apps.backend.app")
sys.modules.setdefault("app", app_module)

from app.infra.http_client import HttpClient  # noqa: E402


@pytest.mark.asyncio
async def test_http_client_returns_json_and_follows_redirects() -> None:
    async def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(200, json={"hello": "world"})

    transport = httpx.MockTransport(handler)
    async with HttpClient(transport=transport) as client:
        response = await client.get("http://test")
        assert response.json() == {"hello": "world"}
        assert client.follow_redirects is True

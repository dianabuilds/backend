import io

import pytest
import pytest_asyncio
from httpx import AsyncClient


@pytest_asyncio.fixture
async def auth_headers(client: AsyncClient, test_user) -> dict:
    resp = await client.post(
        "/auth/login", json={"username": "testuser", "password": "Password123"}
    )
    data = resp.json()
    return {
        "Authorization": f"Bearer {data['access_token']}",
        "X-CSRF-Token": data["csrf_token"],
    }


@pytest.mark.asyncio
async def test_media_upload_valid(client: AsyncClient, auth_headers: dict):
    img = io.BytesIO(b'\x89PNG\r\n\x1a\n')
    resp = await client.post(
        "/media",
        files={"file": ("img.png", img, "image/png")},
        headers=auth_headers,
    )
    assert resp.status_code == 200
    data = resp.json()
    assert "url" in data and data["url"]


@pytest.mark.asyncio
async def test_media_upload_invalid_type(client: AsyncClient, auth_headers: dict):
    file = io.BytesIO(b"hello")
    resp = await client.post(
        "/media",
        files={"file": ("file.txt", file, "text/plain")},
        headers=auth_headers,
    )
    assert resp.status_code == 415


@pytest.mark.asyncio
async def test_media_upload_size_limit(client: AsyncClient, auth_headers: dict):
    big = io.BytesIO(b"a" * (5 * 1024 * 1024 + 1))
    resp = await client.post(
        "/media",
        files={"file": ("big.png", big, "image/png")},
        headers=auth_headers,
    )
    assert resp.status_code == 413

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
async def test_create_node_with_image_content(client: AsyncClient, auth_headers: dict):
    img = io.BytesIO(b'\x89PNG\r\n\x1a\n')
    res = await client.post(
        "/media",
        files={"file": ("img.png", img, "image/png")},
        headers=auth_headers,
    )
    assert res.status_code == 200
    url = res.json()["url"]

    content = {"blocks": [{"type": "image", "data": {"file": {"url": url}}}]}
    payload = {"title": "with image", "content": content, "is_public": True}
    resp = await client.post("/nodes", json=payload, headers=auth_headers)
    assert resp.status_code == 200
    data = resp.json()
    saved = data["content"]["blocks"][0]["data"]["file"]["url"]
    assert saved == url
    assert not saved.startswith("data:")

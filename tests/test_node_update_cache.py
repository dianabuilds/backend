import uuid

import pytest
import pytest_asyncio
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.services.navcache import navcache


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
async def test_patch_node_updates_and_invalidates_cache(
    client: AsyncClient, auth_headers: dict, db_session: AsyncSession, test_user
):
    # Create a node
    payload = {"title": "N1", "content": {}, "is_public": True}
    resp = await client.post("/nodes", json=payload, headers=auth_headers)
    assert resp.status_code == 200
    slug = resp.json()["slug"]

    # Populate caches
    await navcache.set_navigation(test_user.id, slug, "auto", {"mode": "manual", "transitions": []})
    await navcache.set_modes(test_user.id, slug, {"default_mode": "auto", "modes": []})
    await navcache.set_compass(test_user.id, "hash", {"ids": [str(uuid.uuid4())]})
    assert await navcache.get_navigation(test_user.id, slug, "auto") is not None
    assert await navcache.get_modes(test_user.id, slug) is not None
    assert await navcache.get_compass(test_user.id, "hash") is not None

    # Patch node
    patch = {
        "is_public": False,
        "is_visible": False,
        "cover_url": "http://example.com/cover.png",
    }
    resp = await client.patch(f"/nodes/{slug}", json=patch, headers=auth_headers)
    assert resp.status_code == 200
    data = resp.json()
    assert data.get("isPublic") is False
    assert data.get("isVisible") is False
    assert data.get("coverUrl") == "http://example.com/cover.png"

    # Caches should be invalidated
    assert await navcache.get_navigation(test_user.id, slug, "auto") is None
    assert await navcache.get_modes(test_user.id, slug) is None
    assert await navcache.get_compass(test_user.id, "hash") is None

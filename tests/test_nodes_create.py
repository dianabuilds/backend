import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.domains.nodes.infrastructure.models.node import Node
from app.core.security import create_access_token


@pytest.mark.asyncio
async def test_create_node_basic(client: AsyncClient, db_session: AsyncSession, test_user):
    token = create_access_token(test_user.id)
    payload = {
        "title": "Test Node",
        "content_format": "text",
        "nodes": "hello world",
        "is_public": True,
        "is_recommendable": True,
        "tags": ["t1", "t2"],
    }

    resp = await client.post("/nodes", json=payload, headers={"Authorization": f"Bearer {token}"})
    assert resp.status_code == 200, resp.text
    slug = resp.json().get("slug")
    assert isinstance(slug, str) and len(slug) > 0

    # Read the node back and validate a few fields
    resp2 = await client.get(f"/nodes/{slug}", headers={"Authorization": f"Bearer {token}"})
    assert resp2.status_code == 200, resp2.text
    data = resp2.json()
    assert data["title"] == "Test Node"
    assert data["slug"] == slug
    assert data["isPublic"] is True
    # ensure tags saved
    assert set(data.get("tags", [])) == {"t1", "t2"}

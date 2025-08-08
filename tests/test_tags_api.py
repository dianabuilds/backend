import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.node import Node, ContentFormat
from app.services.tags import get_or_create_tags


@pytest.mark.asyncio
async def test_tag_creation_and_listing(client: AsyncClient, db_session: AsyncSession, auth_headers):
    payload = {
        "title": "n1",
        "content_format": "text",
        "content": {},
        "tags": ["forest"],
        "is_public": True,
    }
    resp = await client.post("/nodes", json=payload, headers=auth_headers)
    assert resp.status_code == 200
    # list tags
    resp = await client.get("/tags/")
    assert resp.status_code == 200
    data = resp.json()
    assert any(t["slug"] == "forest" and t["count"] == 1 for t in data)


@pytest.mark.asyncio
async def test_assign_tags_endpoint(client: AsyncClient, db_session: AsyncSession, auth_headers, test_user):
    node = Node(
        title="n2",
        content_format=ContentFormat.text,
        content={},
        is_public=True,
        author_id=test_user.id,
    )
    db_session.add(node)
    await db_session.commit()
    await db_session.refresh(node)

    resp = await client.post(
        f"/nodes/{node.id}/tags",
        json={"tags": ["mirror", "reflection"]},
        headers=auth_headers,
    )
    assert resp.status_code == 200
    data = resp.json()
    assert set(data["tags"]) == {"mirror", "reflection"}


@pytest.mark.asyncio
async def test_filter_nodes_by_tags(client: AsyncClient, db_session: AsyncSession, auth_headers, test_user):
    n1 = Node(
        title="a",
        content_format=ContentFormat.text,
        content={},
        is_public=True,
        author_id=test_user.id,
    )
    n1.tags = await get_or_create_tags(db_session, ["t1", "t2"])
    db_session.add(n1)
    n2 = Node(
        title="b",
        content_format=ContentFormat.text,
        content={},
        is_public=True,
        author_id=test_user.id,
    )
    n2.tags = await get_or_create_tags(db_session, ["t2"])
    db_session.add(n2)
    await db_session.commit()

    resp = await client.get("/nodes", params={"tags": "t1"}, headers=auth_headers)
    assert resp.status_code == 200
    data = resp.json()
    assert len(data) == 1 and data[0]["slug"] == n1.slug

    resp = await client.get(
        "/nodes",
        params={"tags": "t2", "match": "all"},
        headers=auth_headers,
    )
    assert resp.status_code == 200
    data = resp.json()
    assert len(data) == 2

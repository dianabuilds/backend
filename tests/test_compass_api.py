import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

from app.models.node import Node
from app.services.compass_cache import compass_cache


@pytest.mark.asyncio
async def test_compass_api_cache(client: AsyncClient, db_session: AsyncSession, auth_headers, test_user):
    async def create(title: str, tags=None) -> Node:
        resp = await client.post(
            "/nodes",
            json={
                "title": title,
                "content_format": "text",
                "content": title,
                "is_public": True,
                "tags": tags or [],
            },
            headers=auth_headers,
        )
        assert resp.status_code == 200
        slug = resp.json()["slug"]
        result = await db_session.execute(select(Node).where(Node.slug == slug))
        return result.scalars().first()

    base = await create("base", ["a"])
    cand1 = await create("cand1", ["a"])

    resp1 = await client.get(
        f"/navigation/compass?node_id={base.id}&user_id={test_user.id}",
        headers=auth_headers,
    )
    assert resp1.status_code == 200
    data1 = resp1.json()
    assert any(item["id"] == str(cand1.id) for item in data1)

    cand2 = await create("cand2", ["a"])

    resp2 = await client.get(
        f"/navigation/compass?node_id={base.id}&user_id={test_user.id}",
        headers=auth_headers,
    )
    ids2 = {item["id"] for item in resp2.json()}
    assert str(cand2.id) not in ids2

    await compass_cache.invalidate(str(test_user.id), str(base.id))

    resp3 = await client.get(
        f"/navigation/compass?node_id={base.id}&user_id={test_user.id}",
        headers=auth_headers,
    )
    ids3 = {item["id"] for item in resp3.json()}
    assert str(cand2.id) in ids3

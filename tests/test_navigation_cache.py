import pytest
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from httpx import AsyncClient

from app.models.node import Node
from app.engine import navigation_engine
from app.services.navigation_cache import navigation_cache


@pytest.mark.asyncio
async def test_navigation_cached(client: AsyncClient, db_session: AsyncSession, auth_headers, test_user):
    async def create(title: str):
        resp = await client.post(
            "/nodes",
            json={"title": title, "content_format": "text", "content": title, "is_public": True},
            headers=auth_headers,
        )
        assert resp.status_code == 200
        return resp.json()["slug"]

    base = await create("base")
    n1 = await create("n1")
    n2 = await create("n2")

    # patch random and other engines to controlled outputs
    call = {"count": 0}

    async def fake_random(db, exclude_node_id=None, tag_whitelist=None):
        call["count"] += 1
        slug = n1 if call["count"] == 1 else n2
        result = await db.execute(select(Node).where(Node.slug == slug))
        return result.scalars().first()

    async def empty(*args, **kwargs):
        return []

    # apply patches
    monkeypatch = pytest.MonkeyPatch()
    monkeypatch.setattr(navigation_engine, "get_random_node", fake_random)
    monkeypatch.setattr(navigation_engine, "get_compass_nodes", empty)
    monkeypatch.setattr(navigation_engine, "get_echo_transitions", empty)

    # first call generates and caches
    resp1 = await client.get(f"/navigation/{base}", headers=auth_headers)
    assert resp1.status_code == 200
    data1 = resp1.json()

    # second call should use cache (random not called again)
    resp2 = await client.get(f"/navigation/{base}", headers=auth_headers)
    data2 = resp2.json()
    assert data1 == data2
    assert call["count"] == 1

    # invalidate cache and ensure new value is produced
    result = await db_session.execute(select(Node).where(Node.slug == base))
    base_node = result.scalars().first()
    await navigation_cache.invalidate(str(test_user.id), str(base_node.id))

    resp3 = await client.get(f"/navigation/{base}", headers=auth_headers)
    data3 = resp3.json()
    assert data3 != data1
    assert call["count"] == 2

    monkeypatch.undo()

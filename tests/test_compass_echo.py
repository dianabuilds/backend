import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

from app.models.node import Node


@pytest.mark.asyncio
async def test_embedding_saved(client: AsyncClient, db_session: AsyncSession, auth_headers):
    payload = {
        "title": "hello",
        "content": "hello world",
        "is_public": True,
    }
    resp = await client.post("/nodes", json=payload, headers=auth_headers)
    assert resp.status_code == 200
    slug = resp.json()["slug"]

    result = await db_session.execute(select(Node).where(Node.slug == slug))
    node = result.scalars().first()
    assert node.embedding_vector is not None
    assert len(node.embedding_vector) == 384


@pytest.mark.asyncio
async def test_echo_navigation(client: AsyncClient, db_session: AsyncSession, auth_headers):
    # Create base and target nodes
    async def create(title: str, public: bool = True):
        resp = await client.post(
            "/nodes",
            json={
                "title": title,
                "content": title,
                "is_public": public,
            },
            headers=auth_headers,
        )
        assert resp.status_code == 200
        return resp.json()["slug"]

    base = await create("base")
    n1 = await create("node1")
    n2 = await create("node2")
    n3 = await create("node3")
    hidden = await create("hidden", public=False)

    # Record visits
    for _ in range(3):
        await client.post(f"/nodes/{base}/visit/{n1}", headers=auth_headers)
    for _ in range(2):
        await client.post(f"/nodes/{base}/visit/{n2}", headers=auth_headers)
    await client.post(f"/nodes/{base}/visit/{n3}", headers=auth_headers)
    await client.post(f"/nodes/{base}/visit/{hidden}", headers=auth_headers)

    resp = await client.get(f"/nodes/{base}/next?mode=echo", headers=auth_headers)
    assert resp.status_code == 200
    data = resp.json()
    assert len(data["transitions"]) <= 3

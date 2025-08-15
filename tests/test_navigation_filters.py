import pytest
import pytest_asyncio
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

from app.models.node import Node
from app.repositories.compass_repository import CompassRepository


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
async def test_next_filters_private_nodes(
    client: AsyncClient, auth_headers: dict, db_session: AsyncSession
):
    async def create(title: str, public: bool = True) -> str:
        resp = await client.post(
            "/nodes",
            json={"title": title, "content": {}, "is_public": public},
            headers=auth_headers,
        )
        assert resp.status_code == 200
        return resp.json()["slug"]

    base = await create("base")
    public_slug = await create("pub")
    private_slug = await create("priv", public=False)

    # Echo traces
    for _ in range(2):
        await client.post(f"/nodes/{base}/visit/{public_slug}", headers=auth_headers)
    for _ in range(2):
        await client.post(f"/nodes/{base}/visit/{private_slug}", headers=auth_headers)

    # Prepare nodes for compass patch
    result = await db_session.execute(select(Node).where(Node.slug == public_slug))
    public_node = result.scalars().first()
    result = await db_session.execute(select(Node).where(Node.slug == private_slug))
    private_node = result.scalars().first()

    async def fake_similar(self, node, limit, probes):
        return [(private_node, 0.1), (public_node, 0.2)]

    monkeypatch = pytest.MonkeyPatch()
    monkeypatch.setattr(CompassRepository, "get_similar_nodes_pgvector", fake_similar)

    # Compass mode should not return private node
    resp = await client.get(f"/nodes/{base}/next?mode=compass", headers=auth_headers)
    assert resp.status_code == 200
    slugs = [t["slug"] for t in resp.json()["transitions"]]
    assert private_slug not in slugs
    assert public_slug in slugs

    # Echo mode should also exclude private node
    resp = await client.get(f"/nodes/{base}/next?mode=echo", headers=auth_headers)
    assert resp.status_code == 200
    slugs = [t["slug"] for t in resp.json()["transitions"]]
    assert private_slug not in slugs

    monkeypatch.undo()

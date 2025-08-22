import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession


@pytest.mark.asyncio
async def test_node_search_filters_access(client: AsyncClient, auth_headers, db_session: AsyncSession):
    async def create(title: str, tags: list[str], **kwargs) -> str:
        payload = {
            "title": title,
            "nodes": title,
            "is_public": kwargs.get("is_public", True),
            "is_recommendable": kwargs.get("is_recommendable", True),
            "tags": tags,
            "premium_only": kwargs.get("premium_only", False),
        }
        resp = await client.post("/nodes", json=payload, headers=auth_headers)
        assert resp.status_code == 200
        return resp.json()["slug"]

    slug1 = await create("Urban Mystery", ["city", "mystery"])
    await create("Night City", ["city", "night"], premium_only=True)
    await create("Hidden", ["secret"], is_public=False)

    resp = await client.get("/search", params={"tags": "city"})
    assert resp.status_code == 200
    data = resp.json()
    slugs = {d["slug"] for d in data}
    assert slug1 in slugs
    assert len(slugs) == 1

    resp = await client.get("/search", params={"q": "Urban"})
    assert resp.status_code == 200
    slugs = {d["slug"] for d in resp.json()}
    assert slug1 in slugs

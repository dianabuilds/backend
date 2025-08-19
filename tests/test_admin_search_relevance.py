import pytest
from httpx import AsyncClient
from app.core.security import create_access_token
from app.models.user import User


@pytest.mark.asyncio
async def test_relevance_get_requires_auth(client: AsyncClient):
    resp = await client.get("/admin/search/relevance")
    assert resp.status_code == 401


@pytest.mark.asyncio
async def test_relevance_get_ok(client: AsyncClient, admin_user: User):
    token = create_access_token(admin_user.id)
    headers = {"Authorization": f"Bearer {token}"}
    resp = await client.get("/admin/search/relevance", headers=headers)
    assert resp.status_code == 200
    data = resp.json()
    assert "version" in data and "payload" in data


@pytest.mark.asyncio
async def test_relevance_dryrun_ok(client: AsyncClient, admin_user: User):
    token = create_access_token(admin_user.id)
    headers = {"Authorization": f"Bearer {token}"}
    body = {
        "payload": {
            "weights": {"title": 3.0, "body": 1.0, "tags": 1.5, "author": 0.5},
            "boosts": {"freshness": {"half_life_days": 14}, "popularity": {"weight": 1.0}},
            "query": {"fuzziness": "AUTO", "min_should_match": "2<75%", "phrase_slop": 0},
        },
        "dryRun": True,
        "sample": ["test", "quest"],
    }
    resp = await client.put("/admin/search/relevance", headers=headers, json=body)
    assert resp.status_code == 200
    data = resp.json()
    assert "diff" in data

import pytest
import pytest_asyncio
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import create_access_token, get_password_hash
from app.models.user import User


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
async def test_quest_creation_publish_and_progress(
    client: AsyncClient, auth_headers: dict, db_session: AsyncSession
):
    async def create_node(title: str):
        resp = await client.post(
            "/nodes",
            json={"title": title, "content": {}, "is_public": True},
            headers=auth_headers,
        )
        assert resp.status_code == 200
        return resp.json()

    n1 = await create_node("n1")
    n2 = await create_node("n2")
    n3 = await create_node("n3")

    quest_payload = {
        "title": "Quest",
        "entry_node_id": n1["id"],
        "nodes": [n1["id"], n2["id"], n3["id"]],
        "custom_transitions": {
            n1["id"]: {n2["id"]: {"type": "manual"}},
            n2["id"]: {n3["id"]: {"type": "manual"}},
        },
    }
    resp = await client.post("/quests", json=quest_payload, headers=auth_headers)
    assert resp.status_code == 200
    quest_id = resp.json()["id"]

    resp = await client.post(f"/quests/{quest_id}/publish", headers=auth_headers)
    assert resp.status_code == 200
    assert resp.json()["is_draft"] is False

    resp = await client.post(f"/quests/{quest_id}/start", headers=auth_headers)
    assert resp.status_code == 200
    progress = resp.json()
    assert progress["current_node_id"] == n1["id"]

    resp = await client.get(f"/quests/{quest_id}/nodes/{n2['id']}", headers=auth_headers)
    assert resp.status_code == 200
    assert resp.json()["slug"] == n2["slug"]

    resp = await client.get(f"/quests/{quest_id}/progress", headers=auth_headers)
    assert resp.status_code == 200
    assert resp.json()["current_node_id"] == n2["id"]


@pytest.mark.asyncio
async def test_author_e2e_flow(client: AsyncClient, auth_headers: dict, db_session: AsyncSession):
    # Author creates nodes and quest
    async def create_node(title: str):
        resp = await client.post(
            "/nodes",
            json={"title": title, "content": {}, "is_public": True},
            headers=auth_headers,
        )
        assert resp.status_code == 200
        return resp.json()

    n1 = await create_node("a1")
    n2 = await create_node("a2")
    n3 = await create_node("a3")

    quest_payload = {
        "title": "AuthQuest",
        "entry_node_id": n1["id"],
        "nodes": [n1["id"], n2["id"], n3["id"]],
        "custom_transitions": {n1["id"]: {n2["id"]: {"type": "manual"}}, n2["id"]: {n3["id"]: {"type": "manual"}}},
    }
    resp = await client.post("/quests", json=quest_payload, headers=auth_headers)
    quest_id = resp.json()["id"]
    await client.post(f"/quests/{quest_id}/publish", headers=auth_headers)

    # Create viewer user
    viewer = User(
        email="viewer@example.com",
        username="viewer",
        password_hash=get_password_hash("Password123"),
        is_active=True,
    )
    db_session.add(viewer)
    await db_session.commit()
    await db_session.refresh(viewer)
    viewer_token = create_access_token(viewer.id)
    viewer_headers = {"Authorization": f"Bearer {viewer_token}"}

    resp = await client.post(f"/quests/{quest_id}/start", headers=viewer_headers)
    assert resp.status_code == 200

    resp = await client.get(f"/quests/{quest_id}/nodes/{n1['id']}", headers=viewer_headers)
    assert resp.status_code == 200
    resp = await client.get(f"/nodes/{n1['slug']}/next", headers=viewer_headers)
    assert resp.status_code == 200
    slugs = [t["slug"] for t in resp.json()["transitions"]]
    assert n2["slug"] in slugs

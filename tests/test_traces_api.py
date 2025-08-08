import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.node import Node, ContentFormat


@pytest.mark.asyncio
async def test_create_and_list_traces(client: AsyncClient, db_session: AsyncSession, auth_headers, test_user):
    node = Node(
        title="n1",
        content_format=ContentFormat.text,
        content={},
        is_public=True,
        author_id=test_user.id,
    )
    db_session.add(node)
    await db_session.commit()
    await db_session.refresh(node)

    payload = {
        "node_id": str(node.id),
        "kind": "manual",
        "comment": "here",
        "tags": ["mystery"],
        "visibility": "public",
    }
    resp = await client.post("/traces", json=payload, headers=auth_headers)
    assert resp.status_code == 200
    data = resp.json()
    assert data["comment"] == "here"

    payload["visibility"] = "private"
    resp = await client.post("/traces", json=payload, headers=auth_headers)
    assert resp.status_code == 200

    resp = await client.get("/traces", params={"node_id": str(node.id)}, headers=auth_headers)
    assert resp.status_code == 200
    data = resp.json()
    assert len(data) == 1

    resp = await client.get(
        "/traces",
        params={"node_id": str(node.id), "visible_to": "me"},
        headers=auth_headers,
    )
    assert resp.status_code == 200
    data = resp.json()
    assert len(data) == 2

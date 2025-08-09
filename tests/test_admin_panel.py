import pytest
from sqlalchemy.future import select
from app.models.user import User
from app.core.security import get_password_hash
from app.models.node import Node
from app.models.transition import NodeTransition


@pytest.mark.asyncio
async def test_admin_create_and_edit_node(client, db_session):
    admin = User(
        email="admin@example.com",
        username="admin",
        password_hash=get_password_hash("AdminPass123"),
        role="admin",
        is_active=True,
    )
    db_session.add(admin)
    await db_session.commit()

    resp = await client.post(
        "/auth/login",
        json={"username": "admin", "password": "AdminPass123"},
    )
    token = resp.json()["access_token"]

    resp = await client.post(
        "/admin/nodes/new",
        data={
            "title": "Admin Node",
            "content_format": "text",
            "content": "hello",
            "tags": "alpha,beta",
            "is_public": "on",
            "is_visible": "on",
            "allow_feedback": "on",
            "is_recommendable": "on",
        },
        cookies={"token": token},
        follow_redirects=False,
    )
    assert resp.status_code == 303

    resp = await client.get("/nodes", headers={"Authorization": f"Bearer {token}"})
    data = resp.json()
    slug = [n["slug"] for n in data if n["title"] == "Admin Node"][0]

    result = await db_session.execute(select(Node).where(Node.slug == slug))
    node = result.scalars().first()
    assert node is not None

    resp = await client.post(
        f"/admin/nodes/{node.id}/edit",
        data={
            "title": "Updated Node",
            "content_format": "text",
            "content": "world",
            "tags": "alpha",
            "is_public": "on",
            "is_visible": "on",
            "allow_feedback": "on",
            "is_recommendable": "on",
        },
        cookies={"token": token},
        follow_redirects=False,
    )
    assert resp.status_code == 303

    resp = await client.get(f"/nodes/{slug}", headers={"Authorization": f"Bearer {token}"})
    assert resp.json()["title"] == "Updated Node"


@pytest.mark.asyncio
async def test_admin_create_transition(client, db_session):
    admin = User(
        email="admin2@example.com",
        username="admin2",
        password_hash=get_password_hash("AdminPass123"),
        role="admin",
        is_active=True,
    )
    db_session.add(admin)
    await db_session.commit()

    resp = await client.post(
        "/auth/login",
        json={"username": "admin2", "password": "AdminPass123"},
    )
    token = resp.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    resp = await client.post(
        "/nodes",
        json={"title": "n1", "content_format": "text", "content": "a", "is_public": True},
        headers=headers,
    )
    slug1 = resp.json()["slug"]
    resp = await client.post(
        "/nodes",
        json={"title": "n2", "content_format": "text", "content": "b", "is_public": True},
        headers=headers,
    )
    slug2 = resp.json()["slug"]

    result = await db_session.execute(select(Node).where(Node.slug == slug1))
    node1 = result.scalars().first()
    result = await db_session.execute(select(Node).where(Node.slug == slug2))
    node2 = result.scalars().first()

    resp = await client.post(
        "/admin/transitions/new",
        data={
            "from_node": str(node1.id),
            "to_node": str(node2.id),
            "type": "manual",
            "weight": "2",
            "label": "go",
        },
        cookies={"token": token},
        follow_redirects=False,
    )
    assert resp.status_code == 303

    result = await db_session.execute(
        select(NodeTransition).where(
            NodeTransition.from_node_id == node1.id,
            NodeTransition.to_node_id == node2.id,
        )
    )
    transition = result.scalars().first()
    assert transition is not None
    assert transition.weight == 2
    assert transition.label == "go"

import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.node import Node
from app.models.echo_trace import EchoTrace
from app.models.user import User


async def login(client: AsyncClient, username: str, password: str = "Password123") -> dict:
    resp = await client.post("/auth/login", json={"username": username, "password": password})
    token = resp.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


@pytest.mark.asyncio
async def test_anonymize_rbac(client: AsyncClient, db_session: AsyncSession, admin_user: User, moderator_user: User):
    n1 = Node(slug="n1", title="N1", content={}, is_public=True, author_id=admin_user.id)
    n2 = Node(slug="n2", title="N2", content={}, is_public=True, author_id=admin_user.id)
    db_session.add_all([n1, n2])
    await db_session.commit()
    trace = EchoTrace(from_node_id=n1.id, to_node_id=n2.id, user_id=admin_user.id)
    db_session.add(trace)
    await db_session.commit()
    headers_mod = await login(client, "moderator")
    resp = await client.post(f"/admin/echo/{trace.id}/anonymize", headers=headers_mod)
    assert resp.status_code == 403
    headers_admin = await login(client, "admin")
    resp = await client.post(f"/admin/echo/{trace.id}/anonymize", headers=headers_admin)
    assert resp.status_code == 200
    await db_session.refresh(trace)
    assert trace.user_id is None


@pytest.mark.asyncio
async def test_recompute_popularity(client: AsyncClient, db_session: AsyncSession, admin_user: User):
    a = Node(slug="a", title="A", content={}, is_public=True, author_id=admin_user.id)
    b = Node(slug="b", title="B", content={}, is_public=True, author_id=admin_user.id)
    db_session.add_all([a, b])
    await db_session.commit()
    for _ in range(3):
        db_session.add(EchoTrace(from_node_id=a.id, to_node_id=b.id))
    await db_session.commit()
    headers = await login(client, "admin")
    resp = await client.post("/admin/echo/recompute_popularity", json={"node_slugs": ["b"]}, headers=headers)
    assert resp.status_code == 200
    await db_session.refresh(b)
    assert b.popularity_score == 3

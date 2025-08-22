import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.domains.nodes.infrastructure.models.node import Node
from app.domains.navigation.infrastructure.models.transition_models import (
    NodeTrace,
    NodeTraceKind,
)
from app.domains.users.infrastructure.models.user import User


async def login(client: AsyncClient, username: str, password: str = "Password123") -> dict:
    resp = await client.post(
        "/auth/login", json={"username": username, "password": password}
    )
    token = resp.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


@pytest.mark.asyncio
async def test_admin_traces_list_and_anonymize_rbac(
    client: AsyncClient, db_session: AsyncSession, admin_user: User, moderator_user: User
):
    async with db_session.bind.begin() as conn:
        await conn.run_sync(Node.__table__.create)
        await conn.run_sync(NodeTrace.__table__.create)

    node = Node(slug="n1", title="N1", content={}, is_public=True, author_id=admin_user.id)
    db_session.add(node)
    await db_session.commit()

    trace = NodeTrace(node_id=node.id, user_id=admin_user.id, kind=NodeTraceKind.auto)
    db_session.add(trace)
    await db_session.commit()

    headers_mod = await login(client, "moderator")
    resp = await client.get("/admin/traces", headers=headers_mod)
    assert resp.status_code == 200
    assert len(resp.json()) == 1

    resp = await client.post(
        f"/admin/traces/{trace.id}/anonymize", headers=headers_mod
    )
    assert resp.status_code == 403

    headers_admin = await login(client, "admin")
    resp = await client.post(
        f"/admin/traces/{trace.id}/anonymize", headers=headers_admin
    )
    assert resp.status_code == 200
    await db_session.refresh(trace)
    assert trace.user_id is None

    async with db_session.bind.begin() as conn:
        await conn.run_sync(NodeTrace.__table__.drop)
        await conn.run_sync(Node.__table__.drop)


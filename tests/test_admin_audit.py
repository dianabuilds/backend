import asyncio

import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.domains.nodes.infrastructure.models.node import Node
from app.domains.users.infrastructure.models.user import User
from app.domains.admin.infrastructure.models.audit_log import AuditLog
from sqlalchemy.future import select


async def login(client: AsyncClient, username: str, password: str = "Password123") -> dict:
    resp = await client.post("/auth/login", json={"username": username, "password": password})
    token = resp.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


@pytest.mark.asyncio
async def test_audit_log_records_action(client: AsyncClient, db_session: AsyncSession, admin_user: User):
    node = Node(slug="a", title="A", content={}, is_public=True, author_id=admin_user.id)
    db_session.add(node)
    await db_session.commit()
    headers = await login(client, "admin")
    resp = await client.post(
        "/admin/echo/recompute_popularity",
        headers=headers,
        json={"node_slugs": ["a"]},
    )
    assert resp.status_code == 200
    await asyncio.sleep(0.1)
    resp = await client.get("/admin/audit", headers=headers)
    assert resp.status_code == 200
    res = await db_session.execute(select(AuditLog))
    rows = res.scalars().all()
    assert any(log.action == "recompute_popularity" for log in rows)


@pytest.mark.asyncio
async def test_audit_log_rbac(client: AsyncClient, moderator_user: User):
    headers = await login(client, "moderator")
    resp = await client.get("/admin/audit", headers=headers)
    assert resp.status_code == 403

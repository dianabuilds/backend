import asyncio
import json

import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.main import app
from app.domains.admin.api.audit_router import router as admin_audit_router
from app.domains.users.infrastructure.models.user import User
from app.domains.admin.infrastructure.models.audit_log import AuditLog

app.include_router(admin_audit_router)


async def login(client: AsyncClient, username: str, password: str = "Password123") -> dict:
    resp = await client.post("/auth/login", json={"username": username, "password": password})
    token = resp.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


@pytest.mark.asyncio
async def test_audit_log_records_action(
    client: AsyncClient, db_session: AsyncSession, admin_user: User
):
    from app.core.audit_log import log_admin_action

    engine = db_session.bind
    async with engine.begin() as conn:
        await conn.run_sync(AuditLog.__table__.create)
    await log_admin_action(
        db_session,
        actor_id=admin_user.id,
        action="test_action",
        resource_type="node",
        resource_id="a",
    )
    await db_session.commit()
    headers = await login(client, "admin")
    resp = await client.get(
        "/admin/audit", headers={**headers, "accept": "application/json"}
    )
    assert resp.status_code == 200
    data = resp.json()
    assert any(entry["action"] == "test_action" for entry in data)
    async with engine.begin() as conn:
        await conn.run_sync(AuditLog.__table__.drop)


@pytest.mark.asyncio
async def test_audit_log_parses_json_strings(
    client: AsyncClient, db_session: AsyncSession, admin_user: User
):
    engine = db_session.bind
    async with engine.begin() as conn:
        await conn.run_sync(AuditLog.__table__.create)
    log = AuditLog(
        action="stringified",
        before=json.dumps({"a": 1}),
        after=json.dumps({"b": 2}),
    )
    db_session.add(log)
    await db_session.commit()
    headers = await login(client, "admin")
    resp = await client.get(
        "/admin/audit", headers={**headers, "accept": "application/json"}
    )
    assert resp.status_code == 200
    data = resp.json()
    entry = next(item for item in data if item["action"] == "stringified")
    assert entry["before"] == {"a": 1}
    assert entry["after"] == {"b": 2}
    async with engine.begin() as conn:
        await conn.run_sync(AuditLog.__table__.drop)


@pytest.mark.asyncio
async def test_audit_log_rbac(client: AsyncClient, moderator_user: User):
    headers = await login(client, "moderator")
    resp = await client.get(
        "/admin/audit", headers={**headers, "accept": "application/json"}
    )
    assert resp.status_code == 403

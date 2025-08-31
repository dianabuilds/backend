import uuid

import pytest
from sqlalchemy import text

from app.domains.registry import register_domain_routers


async def _create_workspace(db, ws_id, owner_id):
    slug = ws_id[:8]
    sql = (
        "INSERT INTO workspaces (id, name, slug, owner_user_id, settings_json, type, is_system) "
        "VALUES (:id, 'WS', :slug, :owner, :settings, 'team', 0)"
    )
    await db.execute(
        text(sql),
        {
            "id": ws_id,
            "slug": slug,
            "owner": owner_id,
            "settings": '{"limits":{"ai_tokens":1000}}',
        },
    )
    await db.execute(
        text(
            "INSERT INTO workspace_members (workspace_id, user_id, role) VALUES (:ws, :user, 'owner')"
        ),
        {"ws": ws_id, "user": owner_id},
    )


@pytest.mark.asyncio
async def test_usage_by_workspace(client, db_session, auth_headers, test_user):
    register_domain_routers(client._transport.app)  # type: ignore[attr-defined]
    await db_session.execute(
        text("UPDATE users SET role='admin' WHERE id=:id"), {"id": test_user.id}
    )
    ws_id = str(uuid.uuid4())
    await _create_workspace(db_session, ws_id, test_user.id)
    await db_session.execute(
        text(
            "INSERT INTO ai_usage (id, workspace_id, user_id, total_tokens, cost) "
            "VALUES (:id, :ws, :user, 400, 2.0)"
        ),
        {"id": str(uuid.uuid4()), "ws": ws_id, "user": test_user.id},
    )
    await db_session.commit()

    resp = await client.get("/admin/ai/usage/workspaces", headers=auth_headers)
    assert resp.status_code == 200
    data = resp.json()
    assert data[0]["tokens"] == 400


@pytest.mark.asyncio
async def test_workspace_usage_endpoint(client, db_session, auth_headers, test_user):
    register_domain_routers(client._transport.app)  # type: ignore[attr-defined]
    ws_id = str(uuid.uuid4())
    await _create_workspace(db_session, ws_id, test_user.id)
    await db_session.execute(
        text(
            "INSERT INTO ai_usage (id, workspace_id, user_id, total_tokens, cost) "
            "VALUES (:id, :ws, :user, 900, 5.0)"
        ),
        {"id": str(uuid.uuid4()), "ws": ws_id, "user": test_user.id},
    )
    await db_session.commit()

    resp = await client.get(f"/admin/workspaces/{ws_id}/usage", headers=auth_headers)
    assert resp.status_code == 200
    body = resp.json()
    assert body["tokens"] == 900
    assert body["limit"] == 1000

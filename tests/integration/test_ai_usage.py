import uuid

import pytest
from sqlalchemy import text

from app.domains.accounts.api import router as accounts_router
from app.domains.ai.api.usage_router import router as ai_usage_router


async def _create_account(db, account_id: int, owner_id):
    slug = f"a{account_id}"
    sql = (
        "INSERT INTO accounts (id, name, slug, owner_user_id, settings_json, kind, is_system) "
        "VALUES (:id, 'WS', :slug, :owner, :settings, 'team', 0)"
    )
    await db.execute(
        text(sql),
        {
            "id": account_id,
            "slug": slug,
            "owner": owner_id,
            "settings": '{"limits":{"ai_tokens":1000}}',
        },
    )
    await db.execute(
        text(
            "INSERT INTO account_members (account_id, user_id, role) "
            "VALUES (:ws, :user, 'owner')"
        ),
        {"ws": account_id, "user": owner_id},
    )


@pytest.mark.asyncio
async def test_usage_by_account(client, db_session, auth_headers, test_user):
    client._transport.app.include_router(ai_usage_router)  # type: ignore[attr-defined]
    client._transport.app.include_router(accounts_router)  # type: ignore[attr-defined]
    await db_session.execute(
        text("UPDATE users SET role='admin' WHERE id=:id"), {"id": test_user.id}
    )
    account_id = 1
    await _create_account(db_session, account_id, test_user.id)
    await db_session.execute(
        text(
            "INSERT INTO ai_usage (id, workspace_id, user_id, total_tokens, cost) "
            "VALUES (:id, :ws, :user, 400, 2.0)"
        ),
        {"id": str(uuid.uuid4()), "ws": account_id, "user": test_user.id},
    )
    await db_session.commit()

    resp = await client.get("/admin/ai/usage/accounts", headers=auth_headers)
    assert resp.status_code == 200
    data = resp.json()
    assert data[0]["tokens"] == 400


@pytest.mark.asyncio
async def test_account_usage_endpoint(client, db_session, auth_headers, test_user):
    client._transport.app.include_router(ai_usage_router)  # type: ignore[attr-defined]
    client._transport.app.include_router(accounts_router)  # type: ignore[attr-defined]
    account_id = 2
    await _create_account(db_session, account_id, test_user.id)
    await db_session.execute(
        text(
            "INSERT INTO ai_usage (id, workspace_id, user_id, total_tokens, cost) "
            "VALUES (:id, :ws, :user, 900, 5.0)"
        ),
        {"id": str(uuid.uuid4()), "ws": account_id, "user": test_user.id},
    )
    await db_session.commit()

    resp = await client.get(f"/admin/accounts/{account_id}/usage", headers=auth_headers)
    assert resp.status_code == 200
    body = resp.json()
    assert body["tokens"] == 900
    assert body["limit"] == 1000

import pytest
from apps.backend.app.main import app
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession
from tests.integration.conftest import test_engine

from app.domains.accounts.api import router as accounts_router
from app.domains.accounts.infrastructure.models import Account, AccountMember

app.include_router(accounts_router)


@pytest.mark.asyncio
async def test_notification_rules_crud(
    client: AsyncClient, db_session: AsyncSession, auth_headers: dict[str, str]
) -> None:
    # ensure required tables exist
    async with test_engine.begin() as conn:
        await conn.run_sync(Account.__table__.create)
        await conn.run_sync(AccountMember.__table__.create)

    # create account
    payload = {"name": "WS", "slug": "ws"}
    res = await client.post("/admin/accounts", json=payload, headers=auth_headers)
    assert res.status_code == 201
    account_id = res.json()["id"]

    # default rules
    res = await client.get(
        f"/admin/accounts/{account_id}/settings/notifications", headers=auth_headers
    )
    assert res.status_code == 200
    assert res.json() == {"achievement": [], "publish": []}

    # update rules
    rules = {"achievement": ["in-app"], "publish": ["email"]}
    res = await client.put(
        f"/admin/accounts/{account_id}/settings/notifications",
        headers=auth_headers,
        json=rules,
    )
    assert res.status_code == 200
    assert res.json() == rules

    # invalid rules should fail
    bad = {"unknown": ["in-app"]}
    res = await client.put(
        f"/admin/accounts/{account_id}/settings/notifications",
        headers=auth_headers,
        json=bad,
    )
    assert res.status_code == 422

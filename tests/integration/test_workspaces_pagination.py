import pytest
from httpx import AsyncClient
from sqlalchemy import text

from app.domains.accounts.api import router as accounts_router
from app.main import app
from app.security import auth_user

app.include_router(accounts_router)


@pytest.mark.asyncio
async def test_list_accounts_pagination(
    client: AsyncClient,
    db_session,
    test_user,
) -> None:
    app.dependency_overrides[auth_user] = lambda: test_user
    await db_session.execute(
        text("UPDATE users SET role='admin' WHERE id=:id"), {"id": test_user.id}
    )
    await db_session.commit()
    for i in range(3):
        resp = await client.post(
            "/admin/accounts",
            json={"name": f"WS{i}", "slug": f"ws-{i}"},
        )
        assert resp.status_code == 201

    resp = await client.get(
        "/admin/accounts?limit=2",
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["limit"] == 2
    assert len(data["items"]) == 2
    assert data["next_cursor"] is not None

    next_cursor = data["next_cursor"]
    resp = await client.get(
        f"/admin/accounts?cursor={next_cursor}&limit=2",
    )
    assert resp.status_code == 200
    data2 = resp.json()
    assert len(data2["items"]) == 1
    app.dependency_overrides.pop(auth_user, None)

import pytest
from fastapi import FastAPI
from httpx import ASGITransport, AsyncClient

from app.domains.accounts.api import user_router
from app.domains.accounts.application.service import AccountService
from app.providers.db.session import get_db
from app.schemas.accounts import AccountIn
from app.security import auth_user

app = FastAPI()
app.include_router(user_router)


@pytest.mark.asyncio
async def test_list_accounts_for_user(db_session, test_user) -> None:
    app.dependency_overrides[get_db] = lambda: db_session
    app.dependency_overrides[auth_user] = lambda: test_user
    await AccountService.create(db_session, data=AccountIn(name="A1", slug="a1"), owner=test_user)
    await AccountService.create(db_session, data=AccountIn(name="A2", slug="a2"), owner=test_user)
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        resp = await client.get("/accounts/")
    assert resp.status_code == 200
    data = resp.json()
    assert isinstance(data, list)
    assert {item["slug"] for item in data} == {"a1", "a2"}
    app.dependency_overrides.clear()

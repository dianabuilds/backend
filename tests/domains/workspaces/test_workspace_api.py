import pytest
import pytest_asyncio
from uuid import uuid4
from httpx import AsyncClient, ASGITransport
from sqlalchemy.ext.asyncio import AsyncSession

from app.main import app
from app.core.db.session import get_db
from tests.conftest import test_engine
from app.domains.workspaces.infrastructure.models import Workspace, WorkspaceMember


@pytest_asyncio.fixture
async def workspace_tables():
    async with test_engine.begin() as conn:
        await conn.run_sync(Workspace.__table__.create)
        await conn.run_sync(WorkspaceMember.__table__.create)
    yield
    async with test_engine.begin() as conn:
        await conn.run_sync(WorkspaceMember.__table__.drop)
        await conn.run_sync(Workspace.__table__.drop)


@pytest_asyncio.fixture
async def ws_client(db_session: AsyncSession, workspace_tables):
    async def override_get_db():
        yield db_session
    app.dependency_overrides[get_db] = override_get_db
    from app.domains.workspaces.api import router as ws_router
    if not any(r.path.startswith("/admin/workspaces") for r in app.router.routes):
        app.include_router(ws_router)
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        yield client
    app.dependency_overrides.clear()


async def _login(client: AsyncClient, username: str) -> dict:
    resp = await client.post("/auth/login", json={"username": username, "password": "Password123"})
    token = resp.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


@pytest.mark.asyncio
async def test_create_workspace_success(ws_client: AsyncClient, test_user):
    headers = await _login(ws_client, "testuser")
    resp = await ws_client.post(
        "/admin/workspaces", json={"name": "WS", "slug": "ws"}, headers=headers
    )
    assert resp.status_code == 201
    ws_id = resp.json()["id"]
    resp_get = await ws_client.get(f"/admin/workspaces/{ws_id}", headers=headers)
    assert resp_get.status_code == 200


@pytest.mark.asyncio
async def test_update_workspace_forbidden(ws_client: AsyncClient, test_user, moderator_user):
    owner_headers = await _login(ws_client, "testuser")
    resp = await ws_client.post(
        "/admin/workspaces", json={"name": "WS", "slug": "ws"}, headers=owner_headers
    )
    ws_id = resp.json()["id"]
    mod_headers = await _login(ws_client, "moderator")
    resp_upd = await ws_client.patch(
        f"/admin/workspaces/{ws_id}", json={"name": "new"}, headers=mod_headers
    )
    assert resp_upd.status_code == 403


@pytest.mark.asyncio
async def test_get_workspace_not_found(ws_client: AsyncClient, test_user):
    headers = await _login(ws_client, "testuser")
    resp = await ws_client.get(f"/admin/workspaces/{uuid4()}", headers=headers)
    assert resp.status_code == 404


@pytest.mark.asyncio
async def test_create_workspace_validation_error(ws_client: AsyncClient, test_user):
    headers = await _login(ws_client, "testuser")
    resp = await ws_client.post("/admin/workspaces", json={}, headers=headers)
    assert resp.status_code == 422

import pytest
import pytest_asyncio
from uuid import uuid4

from httpx import AsyncClient, ASGITransport
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import create_access_token
from app.main import app
from app.core.db.session import get_db
from app.domains.nodes.models import NodeItem, NodePatch
from app.domains.workspaces.infrastructure.models import Workspace, WorkspaceMember
from app.domains.admin.infrastructure.models.audit_log import AuditLog
from app.domains.users.infrastructure.models.user import User
from app.domains.nodes.content_admin_router import router as content_router

pytest_plugins = ("pytest_asyncio",)


@pytest_asyncio.fixture
async def auth_header(admin_user: User):
    token = create_access_token(admin_user.id)
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture
def include_router():
    if not getattr(app, "_nodes_admin_included", False):
        app.include_router(content_router)
        app._nodes_admin_included = True
    return app


@pytest_asyncio.fixture
async def client_with_nodes(include_router, db_session: AsyncSession):
    async def override_get_db():
        yield db_session
    app.dependency_overrides[get_db] = override_get_db
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        yield client
    app.dependency_overrides.clear()


@pytest.mark.asyncio
async def test_admin_node_flow(client_with_nodes: AsyncClient, db_session: AsyncSession, admin_user: User, auth_header: dict):
    await db_session.run_sync(lambda s: Workspace.__table__.create(s.bind, checkfirst=True))
    await db_session.run_sync(lambda s: WorkspaceMember.__table__.create(s.bind, checkfirst=True))
    await db_session.run_sync(lambda s: AuditLog.__table__.create(s.bind, checkfirst=True))
    await db_session.run_sync(lambda s: NodeItem.__table__.create(s.bind, checkfirst=True))
    await db_session.run_sync(lambda s: NodePatch.__table__.create(s.bind, checkfirst=True))
    ws = Workspace(name="W", slug="w", owner_user_id=admin_user.id)
    db_session.add(ws)
    await db_session.commit()
    await db_session.refresh(ws)

    resp = await client_with_nodes.post(
        f"/admin/nodes/article",
        params={"workspace_id": str(ws.id)},
        headers=auth_header,
    )
    assert resp.status_code == 200
    node_id = resp.json()["id"]

    resp = await client_with_nodes.get(
        f"/admin/nodes/article/{node_id}",
        params={"workspace_id": str(ws.id)},
        headers=auth_header,
    )
    assert resp.status_code == 200

    resp = await client_with_nodes.patch(
        f"/admin/nodes/article/{node_id}",
        params={"workspace_id": str(ws.id)},
        json={"title": "Updated"},
        headers=auth_header,
    )
    assert resp.status_code == 200
    assert resp.json()["title"] == "Updated"

    resp = await client_with_nodes.post(
        f"/admin/nodes/article/{node_id}/validate",
        params={"workspace_id": str(ws.id)},
        headers=auth_header,
    )
    assert resp.status_code == 200

    resp = await client_with_nodes.post(
        f"/admin/nodes/article/{node_id}/publish",
        params={"workspace_id": str(ws.id)},
        headers=auth_header,
    )
    assert resp.status_code == 200
    assert resp.json()["status"] == "published"


@pytest.mark.asyncio
async def test_admin_node_not_found(client_with_nodes: AsyncClient, db_session: AsyncSession, admin_user: User, auth_header: dict):
    await db_session.run_sync(lambda s: Workspace.__table__.create(s.bind, checkfirst=True))
    await db_session.run_sync(lambda s: WorkspaceMember.__table__.create(s.bind, checkfirst=True))
    await db_session.run_sync(lambda s: AuditLog.__table__.create(s.bind, checkfirst=True))
    await db_session.run_sync(lambda s: NodeItem.__table__.create(s.bind, checkfirst=True))
    await db_session.run_sync(lambda s: NodePatch.__table__.create(s.bind, checkfirst=True))
    ws = Workspace(name="W2", slug="w2", owner_user_id=admin_user.id)
    db_session.add(ws)
    await db_session.commit()
    await db_session.refresh(ws)

    missing_id = uuid4()
    resp = await client_with_nodes.get(
        f"/admin/nodes/article/{missing_id}",
        params={"workspace_id": str(ws.id)},
        headers=auth_header,
    )
    assert resp.status_code == 404

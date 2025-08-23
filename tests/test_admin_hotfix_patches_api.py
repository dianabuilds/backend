from uuid import uuid4

import pytest
import pytest_asyncio
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import create_access_token
from app.domains.nodes.dao import NodeItemDAO
from app.domains.nodes.models import NodeItem, NodePatch
from app.domains.workspaces.infrastructure.models import Workspace, WorkspaceMember
from app.schemas.workspaces import WorkspaceRole
from tests.conftest import test_engine


@pytest_asyncio.fixture
async def patch_tables():
    async with test_engine.begin() as conn:
        await conn.run_sync(Workspace.__table__.create)
        await conn.run_sync(WorkspaceMember.__table__.create)
        await conn.run_sync(NodeItem.__table__.create)
        await conn.run_sync(NodePatch.__table__.create)
    yield
    async with test_engine.begin() as conn:
        await conn.run_sync(NodePatch.__table__.drop)
        await conn.run_sync(NodeItem.__table__.drop)
        await conn.run_sync(WorkspaceMember.__table__.drop)
        await conn.run_sync(Workspace.__table__.drop)


@pytest.mark.asyncio
async def test_admin_node_patch_flow(
    client: AsyncClient,
    db_session: AsyncSession,
    admin_user,
    patch_tables,
):
    ws = Workspace(id=uuid4(), name="WS", slug="ws", owner_user_id=admin_user.id)
    db_session.add(ws)
    db_session.add(
        WorkspaceMember(
            workspace_id=ws.id, user_id=admin_user.id, role=WorkspaceRole.owner
        )
    )
    item = NodeItem(
        workspace_id=ws.id,
        type="article",
        slug="art1",
        title="Original",
    )
    db_session.add(item)
    await db_session.commit()

    token = create_access_token(admin_user.id)
    resp = await client.post(
        "/admin/hotfix/patches",
        json={"node_id": str(item.id), "data": {"title": "Patched"}},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert resp.status_code == 200
    patch_id = resp.json()["id"]

    items = await NodeItemDAO.list_by_type(
        db_session, workspace_id=ws.id, node_type="article"
    )
    assert items[0].title == "Patched"

    resp = await client.post(
        f"/admin/hotfix/patches/{patch_id}/revert",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert resp.status_code == 200

    items = await NodeItemDAO.list_by_type(
        db_session, workspace_id=ws.id, node_type="article"
    )
    assert items[0].title == "Original"

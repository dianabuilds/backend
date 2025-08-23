import pytest
import pytest_asyncio
from uuid import uuid4
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import create_access_token
from app.domains.workspaces.infrastructure.models import Workspace, WorkspaceMember
from app.domains.content.models import ContentItem, ContentPatch
from app.domains.content.dao import ContentItemDAO
from app.schemas.workspaces import WorkspaceRole

from tests.conftest import test_engine


@pytest_asyncio.fixture
async def patch_tables():
    async with test_engine.begin() as conn:
        await conn.run_sync(Workspace.__table__.create)
        await conn.run_sync(WorkspaceMember.__table__.create)
        await conn.run_sync(ContentItem.__table__.create)
        await conn.run_sync(ContentPatch.__table__.create)
    yield
    async with test_engine.begin() as conn:
        await conn.run_sync(ContentPatch.__table__.drop)
        await conn.run_sync(ContentItem.__table__.drop)
        await conn.run_sync(WorkspaceMember.__table__.drop)
        await conn.run_sync(Workspace.__table__.drop)


@pytest.mark.asyncio
async def test_admin_content_patch_flow(
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
    item = ContentItem(
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
        json={"content_id": str(item.id), "data": {"title": "Patched"}},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert resp.status_code == 200
    patch_id = resp.json()["id"]

    items = await ContentItemDAO.list_by_type(
        db_session, workspace_id=ws.id, content_type="article"
    )
    assert items[0].title == "Patched"

    resp = await client.post(
        f"/admin/hotfix/patches/{patch_id}/revert",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert resp.status_code == 200

    items = await ContentItemDAO.list_by_type(
        db_session, workspace_id=ws.id, content_type="article"
    )
    assert items[0].title == "Original"

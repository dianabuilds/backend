import pytest
import pytest_asyncio
from sqlalchemy.ext.asyncio import AsyncSession

from app.domains.workspaces.infrastructure.dao import WorkspaceDAO, WorkspaceMemberDAO
from app.domains.workspaces.infrastructure.models import Workspace, WorkspaceMember
from app.schemas.workspaces import WorkspaceRole
from tests.conftest import test_engine


@pytest_asyncio.fixture
async def workspace_tables():
    async with test_engine.begin() as conn:
        await conn.run_sync(Workspace.__table__.create)
        await conn.run_sync(WorkspaceMember.__table__.create)
    yield
    async with test_engine.begin() as conn:
        await conn.run_sync(WorkspaceMember.__table__.drop)
        await conn.run_sync(Workspace.__table__.drop)


@pytest.mark.asyncio
async def test_workspace_crud(db_session: AsyncSession, workspace_tables, test_user):
    ws = await WorkspaceDAO.create(
        db_session,
        name="WS1",
        slug="ws1",
        owner_user_id=test_user.id,
    )
    await WorkspaceMemberDAO.add(
        db_session,
        workspace_id=ws.id,
        user_id=test_user.id,
        role=WorkspaceRole.owner,
    )
    await db_session.commit()
    assert ws.id is not None

    loaded = await WorkspaceDAO.get(db_session, ws.id)
    assert loaded and loaded.name == "WS1"

    await WorkspaceDAO.update(db_session, loaded, name="WS2", slug="ws2")
    await db_session.commit()
    await db_session.refresh(loaded)
    assert loaded.name == "WS2"
    assert loaded.slug == "ws2"

    result = await WorkspaceDAO.list_for_user(db_session, test_user.id)
    assert {w.slug for w in result} == {"ws2"}

    await WorkspaceDAO.delete(db_session, loaded)
    await db_session.commit()
    assert await WorkspaceDAO.get(db_session, ws.id) is None


@pytest.mark.asyncio
async def test_list_for_user_permissions(
    db_session: AsyncSession, workspace_tables, test_user, admin_user
):
    ws1 = await WorkspaceDAO.create(
        db_session, name="A", slug="a", owner_user_id=test_user.id
    )
    ws2 = await WorkspaceDAO.create(
        db_session, name="B", slug="b", owner_user_id=admin_user.id
    )
    await WorkspaceMemberDAO.add(
        db_session, workspace_id=ws1.id, user_id=test_user.id, role=WorkspaceRole.owner
    )
    await WorkspaceMemberDAO.add(
        db_session, workspace_id=ws2.id, user_id=admin_user.id, role=WorkspaceRole.owner
    )
    await WorkspaceMemberDAO.add(
        db_session, workspace_id=ws2.id, user_id=test_user.id, role=WorkspaceRole.viewer
    )
    await db_session.commit()

    items = await WorkspaceDAO.list_for_user(db_session, test_user.id)
    assert {w.slug for w in items} == {"a", "b"}

    items_admin = await WorkspaceDAO.list_for_user(db_session, admin_user.id)
    assert {w.slug for w in items_admin} == {"b"}


@pytest.mark.asyncio
async def test_workspace_member_crud(
    db_session: AsyncSession, workspace_tables, test_user, admin_user
):
    ws = await WorkspaceDAO.create(
        db_session, name="C", slug="c", owner_user_id=admin_user.id
    )
    await db_session.commit()

    member = await WorkspaceMemberDAO.add(
        db_session, workspace_id=ws.id, user_id=test_user.id, role=WorkspaceRole.viewer
    )
    await db_session.commit()
    assert member.role == WorkspaceRole.viewer

    fetched = await WorkspaceMemberDAO.get(
        db_session, workspace_id=ws.id, user_id=test_user.id
    )
    assert fetched is not None

    await WorkspaceMemberDAO.update_role(
        db_session, workspace_id=ws.id, user_id=test_user.id, role=WorkspaceRole.editor
    )
    await db_session.commit()
    fetched = await WorkspaceMemberDAO.get(
        db_session, workspace_id=ws.id, user_id=test_user.id
    )
    assert fetched and fetched.role == WorkspaceRole.editor

    members = await WorkspaceMemberDAO.list(db_session, workspace_id=ws.id)
    assert len(members) == 1 and members[0].user_id == test_user.id

    await WorkspaceMemberDAO.remove(
        db_session, workspace_id=ws.id, user_id=test_user.id
    )
    await db_session.commit()
    assert (
        await WorkspaceMemberDAO.get(
            db_session, workspace_id=ws.id, user_id=test_user.id
        )
        is None
    )

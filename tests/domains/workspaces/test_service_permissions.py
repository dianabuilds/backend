import pytest
import pytest_asyncio
from uuid import uuid4
from fastapi import HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from tests.conftest import test_engine
from app.domains.workspaces.infrastructure.models import Workspace, WorkspaceMember
from app.domains.workspaces.application.service import require_ws_editor, require_ws_owner
from app.schemas.workspaces import WorkspaceRole


@pytest_asyncio.fixture
async def workspace_setup():
    async with test_engine.begin() as conn:
        await conn.run_sync(Workspace.__table__.create)
        await conn.run_sync(WorkspaceMember.__table__.create)
    yield
    async with test_engine.begin() as conn:
        await conn.run_sync(WorkspaceMember.__table__.drop)
        await conn.run_sync(Workspace.__table__.drop)


@pytest.mark.asyncio
async def test_require_ws_editor(db_session: AsyncSession, workspace_setup, test_user, moderator_user):
    ws = Workspace(id=uuid4(), name="WS", slug="ws", owner_user_id=test_user.id)
    db_session.add(ws)
    db_session.add(
        WorkspaceMember(
            workspace_id=ws.id, user_id=test_user.id, role=WorkspaceRole.owner
        )
    )
    await db_session.commit()

    member = await require_ws_editor(ws.id, user=test_user, db=db_session)
    assert member and member.role == WorkspaceRole.owner

    with pytest.raises(HTTPException) as exc:
        await require_ws_editor(ws.id, user=moderator_user, db=db_session)
    assert exc.value.status_code == 403


@pytest.mark.asyncio
async def test_require_ws_owner(db_session: AsyncSession, workspace_setup, test_user, moderator_user):
    ws = Workspace(id=uuid4(), name="WS", slug="ws", owner_user_id=test_user.id)
    db_session.add(ws)
    db_session.add_all(
        [
            WorkspaceMember(
                workspace_id=ws.id, user_id=test_user.id, role=WorkspaceRole.owner
            ),
            WorkspaceMember(
                workspace_id=ws.id, user_id=moderator_user.id, role=WorkspaceRole.editor
            ),
        ]
    )
    await db_session.commit()

    member = await require_ws_owner(ws.id, user=test_user, db=db_session)
    assert member and member.role == WorkspaceRole.owner

    with pytest.raises(HTTPException) as exc:
        await require_ws_owner(ws.id, user=moderator_user, db=db_session)
    assert exc.value.status_code == 403

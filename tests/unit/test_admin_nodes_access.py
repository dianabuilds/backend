import importlib
import sys
import uuid
from types import SimpleNamespace

import pytest
import sqlalchemy as sa
from fastapi import HTTPException
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker

# Ensure "app" package resolves correctly
app_module = importlib.import_module("apps.backend.app")
sys.modules.setdefault("app", app_module)

from app.domains.nodes.application.node_service import NodeService  # noqa: E402
from app.domains.nodes.models import NodeItem, NodePatch  # noqa: E402
from app.domains.tags.models import Tag  # noqa: E402
from app.domains.workspaces.infrastructure.models import (  # noqa: E402
    Workspace,
    WorkspaceMember,
)
from app.schemas.nodes_common import NodeType  # noqa: E402
from app.schemas.workspaces import WorkspaceRole  # noqa: E402
from app.security import (  # noqa: E402
    require_ws_editor,
    require_ws_guest,
    require_ws_viewer,
)

users_table = NodeItem.__table__.metadata.tables["users"]


@pytest.mark.asyncio
async def test_get_node_respects_workspace() -> None:
    engine = create_async_engine("sqlite+aiosqlite:///:memory:")
    async with engine.begin() as conn:
        await conn.run_sync(users_table.create)
        await conn.run_sync(Workspace.__table__.create)
        await conn.run_sync(WorkspaceMember.__table__.create)
        await conn.run_sync(Tag.__table__.create)
        await conn.run_sync(NodeItem.__table__.create)
        await conn.run_sync(NodePatch.__table__.create)
    async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

    async with async_session() as session:
        user_id = uuid.uuid4()
        await session.execute(sa.insert(users_table).values(id=str(user_id)))
        ws1 = Workspace(id=uuid.uuid4(), name="W1", slug="w1", owner_user_id=user_id)
        ws2 = Workspace(id=uuid.uuid4(), name="W2", slug="w2", owner_user_id=user_id)
        session.add_all([ws1, ws2])
        await session.commit()

        node = NodeItem(
            id=uuid.uuid4(),
            workspace_id=ws1.id,
            type=NodeType.quest.value,
            slug="node-1",
            title="Node",
            created_by_user_id=user_id,
        )
        session.add(node)
        await session.commit()

        svc = NodeService(session)
        item = await svc.get(ws1.id, node.id)
        assert item.id == node.id

        with pytest.raises(HTTPException):
            await svc.get(ws2.id, node.id)


@pytest.mark.asyncio
async def test_require_ws_editor_roles() -> None:
    engine = create_async_engine("sqlite+aiosqlite:///:memory:")
    async with engine.begin() as conn:
        await conn.run_sync(users_table.create)
        await conn.run_sync(Workspace.__table__.create)
        await conn.run_sync(WorkspaceMember.__table__.create)
    async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

    async with async_session() as session:
        user_id = uuid.uuid4()
        await session.execute(sa.insert(users_table).values(id=str(user_id)))
        ws = Workspace(id=uuid.uuid4(), name="W", slug="w", owner_user_id=user_id)
        session.add(ws)
        await session.commit()

        user = SimpleNamespace(id=user_id, role="user")

        with pytest.raises(HTTPException):
            await require_ws_editor(workspace_id=ws.id, user=user, db=session)

        member = WorkspaceMember(workspace_id=ws.id, user_id=user_id, role=WorkspaceRole.viewer)
        session.add(member)
        await session.commit()
        with pytest.raises(HTTPException):
            await require_ws_editor(workspace_id=ws.id, user=user, db=session)

        member.role = WorkspaceRole.editor
        await session.commit()
        res = await require_ws_editor(workspace_id=ws.id, user=user, db=session)
        assert res.role == WorkspaceRole.editor


@pytest.mark.asyncio
async def test_require_ws_viewer_roles() -> None:
    engine = create_async_engine("sqlite+aiosqlite:///:memory:")
    async with engine.begin() as conn:
        await conn.run_sync(users_table.create)
        await conn.run_sync(Workspace.__table__.create)
        await conn.run_sync(WorkspaceMember.__table__.create)
    async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

    async with async_session() as session:
        user_id = uuid.uuid4()
        await session.execute(sa.insert(users_table).values(id=str(user_id)))
        ws = Workspace(id=uuid.uuid4(), name="W", slug="w", owner_user_id=user_id)
        session.add(ws)
        await session.commit()

        user = SimpleNamespace(id=user_id, role="user")

        with pytest.raises(HTTPException):
            await require_ws_viewer(workspace_id=ws.id, user=user, db=session)

        member = WorkspaceMember(workspace_id=ws.id, user_id=user_id, role=WorkspaceRole.viewer)
        session.add(member)
        await session.commit()
        res = await require_ws_viewer(workspace_id=ws.id, user=user, db=session)
        assert res.role == WorkspaceRole.viewer


@pytest.mark.asyncio
async def test_require_ws_guest_roles() -> None:
    engine = create_async_engine("sqlite+aiosqlite:///:memory:")
    async with engine.begin() as conn:
        await conn.run_sync(users_table.create)
        await conn.run_sync(Workspace.__table__.create)
        await conn.run_sync(WorkspaceMember.__table__.create)
    async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

    async with async_session() as session:
        user_id = uuid.uuid4()
        await session.execute(sa.insert(users_table).values(id=str(user_id)))
        ws = Workspace(id=uuid.uuid4(), name="W", slug="w", owner_user_id=user_id)
        session.add(ws)
        await session.commit()

        user = SimpleNamespace(id=user_id, role="user")

        with pytest.raises(HTTPException):
            await require_ws_guest(workspace_id=ws.id, user=user, db=session)

        member = WorkspaceMember(workspace_id=ws.id, user_id=user_id, role=WorkspaceRole.viewer)
        session.add(member)
        await session.commit()
        res = await require_ws_guest(workspace_id=ws.id, user=user, db=session)
        assert res.role == WorkspaceRole.viewer

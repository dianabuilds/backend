import uuid
import importlib
import sys
import asyncio
from pathlib import Path
from types import SimpleNamespace

import pytest
from fastapi import HTTPException
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker
import sqlalchemy as sa

# Ensure "app" package resolves correctly
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
app_module = importlib.import_module("apps.backend.app")
sys.modules.setdefault("app", app_module)

from app.domains.workspaces.infrastructure.models import Workspace, WorkspaceMember  # noqa: E402
from app.domains.nodes.models import NodeItem, NodePatch  # noqa: E402
from app.domains.tags.models import Tag  # noqa: E402
from app.domains.nodes.application.node_service import NodeService  # noqa: E402
from app.domains.nodes.infrastructure.models.node import Node  # noqa: E402
from app.domains.tags.infrastructure.models.tag_models import NodeTag  # noqa: E402
from app.domains.nodes.infrastructure.repositories.node_repository import (
    NodeRepositoryAdapter,
)  # noqa: E402
from app.security import require_ws_editor, require_ws_viewer, require_ws_guest  # noqa: E402
from app.schemas.nodes_common import NodeType  # noqa: E402
from app.schemas.workspaces import WorkspaceRole  # noqa: E402

users_table = NodeItem.__table__.metadata.tables["users"]


@pytest.mark.asyncio
async def test_validate_node_respects_workspace() -> None:
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
            type=NodeType.article.value,
            slug="node-1",
            title="Node",
            created_by_user_id=user_id,
        )
        session.add(node)
        await session.commit()

        svc = NodeService(session)
        report = await svc.validate(ws1.id, NodeType.article, node.id)
        assert hasattr(report, "errors")

        with pytest.raises(HTTPException):
            await svc.validate(ws2.id, NodeType.article, node.id)


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

        member = WorkspaceMember(
            workspace_id=ws.id, user_id=user_id, role=WorkspaceRole.viewer
        )
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

        member = WorkspaceMember(
            workspace_id=ws.id, user_id=user_id, role=WorkspaceRole.viewer
        )
        session.add(member)
        await session.commit()
        res = await require_ws_guest(workspace_id=ws.id, user=user, db=session)
        assert res.role == WorkspaceRole.viewer


def test_set_tags_is_scoped_by_workspace() -> None:
    async def _run() -> None:
        engine = create_async_engine("sqlite+aiosqlite:///:memory:")
        async with engine.begin() as conn:
            await conn.run_sync(users_table.create)
            await conn.run_sync(Workspace.__table__.create)
            await conn.run_sync(Tag.__table__.create)
            await conn.run_sync(Node.__table__.create)
            await conn.run_sync(NodeTag.__table__.create)
        async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

        async with async_session() as session:
            user_id = uuid.uuid4()
            await session.execute(sa.insert(users_table).values(id=str(user_id)))
            ws1 = Workspace(id=uuid.uuid4(), name="W1", slug="w1", owner_user_id=user_id)
            ws2 = Workspace(id=uuid.uuid4(), name="W2", slug="w2", owner_user_id=user_id)
            session.add_all([ws1, ws2])
            await session.commit()

            tag_ws2 = Tag(slug="shared", name="Shared", workspace_id=ws2.id)
            session.add(tag_ws2)
            await session.commit()

            node = Node(
                id=uuid.uuid4(),
                workspace_id=ws1.id,
                slug="node",
                title="N",
                content={},
                media=[],
                author_id=user_id,
            )
            session.add(node)
            await session.commit()

            repo = NodeRepositoryAdapter(session)
            await repo.set_tags(node, ["shared"], actor_id=user_id)

            link = await session.execute(
                sa.select(NodeTag).where(NodeTag.node_id == node.id)
            )
            tag_id = link.scalars().first().tag_id
            tag = await session.get(Tag, tag_id)
            assert tag.workspace_id == ws1.id

    asyncio.run(_run())

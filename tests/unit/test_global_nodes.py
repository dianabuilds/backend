from __future__ import annotations

import os
import uuid

import pytest
import pytest_asyncio
import sqlalchemy as sa
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker

os.environ.setdefault("TESTING", "true")

from app.domains.nodes.application.node_service import NodeService
from app.domains.nodes.dao import NodeItemDAO
from app.domains.nodes.infrastructure.models.node import Node
from app.domains.nodes.infrastructure.repositories.node_repository import (
    NodeRepository,
)
from app.domains.nodes.models import NodeItem, NodePatch
from app.domains.tags.infrastructure.models.tag_models import NodeTag
from app.domains.tags.models import ContentTag, Tag
from app.domains.users.infrastructure.models.user import User
from app.domains.workspaces.infrastructure.models import Workspace
from app.schemas.nodes_common import Status, Visibility


@pytest_asyncio.fixture()
async def db() -> AsyncSession:
    engine = create_async_engine("sqlite+aiosqlite:///:memory:")
    async with engine.begin() as conn:
        await conn.run_sync(User.__table__.create)
        await conn.run_sync(Workspace.__table__.create)
        await conn.run_sync(Tag.__table__.create)
        await conn.run_sync(NodeTag.__table__.create)
        await conn.run_sync(ContentTag.__table__.create)
        Node.__table__.c.id.type = sa.Integer()
        Node.__table__.c.workspace_id.nullable = True
        await conn.run_sync(Node.__table__.create)
        NodeItem.__table__.c.workspace_id.nullable = True
        await conn.run_sync(NodeItem.__table__.create)
        await conn.run_sync(NodePatch.__table__.create)
    async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    async with async_session() as session:
        yield session


@pytest.mark.asyncio
async def test_node_service_handles_global_and_workspace_nodes(
    db: AsyncSession,
) -> None:
    user_id = uuid.uuid4()
    ws = Workspace(id=uuid.uuid4(), name="W", slug="w", owner_user_id=user_id)
    db.add_all([User(id=user_id), ws])
    await db.commit()

    global_item = await NodeItemDAO.create(
        db,
        id=1,
        workspace_id=None,
        type="quest",
        slug="g",
        title="Global",
        created_by_user_id=user_id,
        status=Status.draft,
        visibility=Visibility.private,
        version=1,
    )
    ws_item = await NodeItemDAO.create(
        db,
        id=2,
        workspace_id=ws.id,
        type="quest",
        slug="w",
        title="Workspace",
        created_by_user_id=user_id,
        status=Status.draft,
        visibility=Visibility.private,
        version=1,
    )
    tag = Tag(id=uuid.uuid4(), slug="t1", name="T1", workspace_id=ws.id)
    db.add(tag)
    await db.flush()
    await NodeItemDAO.attach_tag(
        db, node_id=ws_item.id, tag_id=tag.id, workspace_id=ws.id
    )
    await db.commit()

    svc = NodeService(db)
    global_list = await svc.list(None)
    assert [i.id for i in global_list] == [global_item.id]
    workspace_list = await svc.list(ws.id)
    assert [i.id for i in workspace_list] == [ws_item.id]
    assert [t.slug for t in workspace_list[0].tags] == ["t1"]

    fetched = await svc.get(None, global_item.id)
    assert fetched.id == global_item.id
    fetched_ws = await svc.get(ws.id, global_item.id)
    assert fetched_ws.id == global_item.id


@pytest.mark.asyncio
async def test_node_repository_adapter_respects_workspace_filter(
    db: AsyncSession,
) -> None:
    user_id = uuid.uuid4()
    ws = Workspace(id=uuid.uuid4(), name="W", slug="w", owner_user_id=user_id)
    db.add_all([User(id=user_id), ws])
    await db.commit()

    global_node = Node(
        slug="gn",
        title="GN",
        author_id=user_id,
        workspace_id=None,
        created_by_user_id=user_id,
    )
    ws_node = Node(
        slug="wn",
        title="WN",
        author_id=user_id,
        workspace_id=ws.id,
        created_by_user_id=user_id,
    )
    db.add_all([global_node, ws_node])
    await db.commit()

    repo = NodeRepository(db)
    assert await repo.get_by_slug("gn", None) is not None
    assert await repo.get_by_slug("gn", ws.id) is None
    assert await repo.get_by_slug("wn", ws.id) is not None
    assert await repo.get_by_slug("wn", None) is None

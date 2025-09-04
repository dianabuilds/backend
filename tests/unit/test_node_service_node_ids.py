from __future__ import annotations

import os
import uuid

import pytest
import pytest_asyncio
import sqlalchemy as sa
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker

# Ensure app package resolves and run in testing mode
os.environ.setdefault("TESTING", "true")

from app.domains.nodes.application.node_service import NodeService
from app.domains.nodes.dao import NodeItemDAO
from app.domains.nodes.infrastructure.models.node import Node
from app.domains.nodes.models import NodeItem, NodePatch
from app.domains.users.infrastructure.models.user import User
from app.domains.workspaces.infrastructure.models import Workspace
from app.schemas.nodes_common import Status, Visibility


@pytest_asyncio.fixture()
async def db() -> AsyncSession:
    engine = create_async_engine("sqlite+aiosqlite:///:memory:")
    async with engine.begin() as conn:
        await conn.run_sync(User.__table__.create)
        await conn.run_sync(Workspace.__table__.create)
        Node.__table__.c.id.type = sa.Integer()  # ensure autoincrement works in SQLite
        await conn.run_sync(Node.__table__.create)
        await conn.run_sync(NodeItem.__table__.create)
        await conn.run_sync(NodePatch.__table__.create)
    async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    async with async_session() as session:
        yield session


@pytest.mark.asyncio
async def test_create_assigns_integer_node_id(db: AsyncSession) -> None:
    user_id = uuid.uuid4()
    ws = Workspace(id=uuid.uuid4(), name="W", slug="w", owner_user_id=user_id)
    db.add_all([User(id=user_id), ws])
    await db.commit()
    service = NodeService(db)
    item = await service.create(ws.id, actor_id=user_id)
    assert item.node_id is not None
    assert isinstance(item.node_id, int)
    assert item.node_id != item.id
    node = await db.get(Node, item.node_id)
    assert node is not None


@pytest.mark.asyncio
async def test_publish_creates_integer_node_id(db: AsyncSession) -> None:
    user_id = uuid.uuid4()
    ws = Workspace(id=uuid.uuid4(), name="W", slug="w", owner_user_id=user_id)
    db.add_all([User(id=user_id), ws])
    await db.commit()
    item = await NodeItemDAO.create(
        db,
        workspace_id=ws.id,
        type="quest",
        slug="s",
        title="t",
        created_by_user_id=user_id,
        status=Status.draft,
        visibility=Visibility.private,
        version=1,
    )
    await db.commit()
    service = NodeService(db)
    published = await service.publish(ws.id, item.id, actor_id=user_id)
    assert published.node_id is not None
    assert isinstance(published.node_id, int)
    assert published.node_id != published.id
    node = await db.get(Node, published.node_id)
    assert node is not None


@pytest.mark.asyncio
async def test_update_creates_integer_node_id(db: AsyncSession) -> None:
    user_id = uuid.uuid4()
    ws = Workspace(id=uuid.uuid4(), name="W", slug="w", owner_user_id=user_id)
    db.add_all([User(id=user_id), ws])
    await db.commit()
    item = await NodeItemDAO.create(
        db,
        workspace_id=ws.id,
        type="quest",
        slug="u",
        title="t",
        created_by_user_id=user_id,
        status=Status.draft,
        visibility=Visibility.private,
        version=1,
    )
    await db.commit()
    service = NodeService(db)
    updated = await service.update(ws.id, item.id, {}, actor_id=user_id)
    assert updated.node_id is not None
    assert isinstance(updated.node_id, int)
    assert updated.node_id != updated.id
    node = await db.get(Node, updated.node_id)
    assert node is not None

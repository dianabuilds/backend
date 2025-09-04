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
from app.domains.nodes.models import NodeItem, NodePatch
from app.domains.quests.infrastructure.models.navigation_cache_models import (
    NavigationCache,
)
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
        await conn.run_sync(ContentTag.__table__.create)
        await conn.run_sync(NodeTag.__table__.create)
        Node.__table__.c.id.type = sa.Integer()
        await conn.run_sync(Node.__table__.create)
        await conn.run_sync(NodeItem.__table__.create)
        await conn.run_sync(NodePatch.__table__.create)
        await conn.run_sync(NavigationCache.__table__.create)
    async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    async with async_session() as session:
        yield session


@pytest.mark.asyncio
async def test_publish_sets_node_status(db: AsyncSession) -> None:
    user_id = uuid.uuid4()
    ws = Workspace(id=uuid.uuid4(), name="W", slug="w", owner_user_id=user_id)
    db.add_all([User(id=user_id), ws])
    await db.commit()
    item = await NodeItemDAO.create(
        db,
        id=1,
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
    svc = NodeService(db)
    await svc.publish(ws.id, item.id, actor_id=user_id)
    refreshed_item = await db.get(NodeItem, item.id)
    node = await db.get(Node, refreshed_item.node_id)
    assert refreshed_item.status == Status.published
    assert node.status == Status.published


@pytest.mark.asyncio
async def test_unpublish_sets_draft_status(db: AsyncSession) -> None:
    user_id = uuid.uuid4()
    ws = Workspace(id=uuid.uuid4(), name="W", slug="w", owner_user_id=user_id)
    db.add_all([User(id=user_id), ws])
    await db.commit()
    item = await NodeItemDAO.create(
        db,
        id=1,
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
    svc = NodeService(db)
    await svc.publish(ws.id, item.id, actor_id=user_id)
    await svc.update(ws.id, item.id, {"isPublic": False}, actor_id=user_id)
    refreshed_item = await db.get(NodeItem, item.id)
    node = await db.get(Node, refreshed_item.node_id)
    assert refreshed_item.status == Status.draft
    assert node.status == Status.draft
    assert refreshed_item.visibility == Visibility.private
    assert node.visibility == Visibility.private

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

import hashlib

from slugify import slugify

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
        from app.domains.quests.infrastructure.models.navigation_cache_models import (
            NavigationCache,
        )

        await conn.run_sync(NavigationCache.__table__.create)
    async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    async with async_session() as session:
        yield session


@pytest.mark.asyncio
async def test_update_syncs_slug_between_item_and_node(db: AsyncSession) -> None:
    user_id = uuid.uuid4()
    ws = Workspace(id=uuid.uuid4(), name="W", slug="w", owner_user_id=user_id)
    node = Node(
        workspace_id=ws.id,
        slug="old",
        title="t",
        author_id=user_id,
        status=Status.draft,
        visibility=Visibility.private,
        created_by_user_id=user_id,
        updated_by_user_id=user_id,
    )
    db.add_all([User(id=user_id), ws, node])
    await db.commit()

    item = await NodeItemDAO.create(
        db,
        id=1,
        workspace_id=ws.id,
        type="quest",
        slug="old",
        title="t",
        created_by_user_id=user_id,
        status=Status.draft,
        visibility=Visibility.private,
        version=1,
        node_id=node.id,
    )
    await db.commit()

    service = NodeService(db)
    updated = await service.update(ws.id, item.id, {"slug": "new"}, actor_id=user_id)
    expected = hashlib.sha256(slugify("new").encode()).hexdigest()[:16]
    assert updated.slug == expected
    node_db = await db.get(Node, node.id)
    assert node_db.slug == expected

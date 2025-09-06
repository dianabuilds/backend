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

from app.domains.nodes.application.node_service import HEX_RE, NodeService  # noqa: E402
from app.domains.nodes.infrastructure.models.node import Node  # noqa: E402
from app.domains.nodes.models import NodeItem, NodePatch  # noqa: E402
from app.domains.tags.models import ContentTag, Tag  # noqa: E402
from app.domains.users.infrastructure.models.user import User  # noqa: E402
from app.domains.workspaces.infrastructure.models import Workspace  # noqa: E402


@pytest_asyncio.fixture()
async def db() -> AsyncSession:
    engine = create_async_engine("sqlite+aiosqlite:///:memory:")
    async with engine.begin() as conn:
        await conn.run_sync(User.__table__.create)
        await conn.run_sync(Workspace.__table__.create)
        Node.__table__.c.id.type = sa.Integer()  # ensure autoincrement works in SQLite
        await conn.run_sync(Node.__table__.create)
        NodeItem.__table__.c.id_bigint.type = sa.Integer()
        await conn.run_sync(NodeItem.__table__.create)
        NodePatch.__table__.c.id_bigint.type = sa.Integer()
        await conn.run_sync(NodePatch.__table__.create)
        await conn.run_sync(Tag.__table__.create)
        await conn.run_sync(ContentTag.__table__.create)
        from app.domains.quests.infrastructure.models.navigation_cache_models import (
            NavigationCache,
        )

        await conn.run_sync(NavigationCache.__table__.create)
    async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    async with async_session() as session:
        yield session


@pytest.mark.asyncio
async def test_create_without_slug_generates_slug(db: AsyncSession) -> None:
    user_id = uuid.uuid4()
    ws = Workspace(id=uuid.uuid4(), name="W", slug="w", owner_user_id=user_id)
    db.add_all([User(id=user_id), ws])
    await db.commit()
    svc = NodeService(db)
    item = await svc.create(ws.id, actor_id=user_id)
    assert HEX_RE.fullmatch(item.slug)


@pytest.mark.asyncio
async def test_create_twice_same_title_generates_unique_slugs(db: AsyncSession) -> None:
    user_id = uuid.uuid4()
    ws = Workspace(id=uuid.uuid4(), name="W", slug="w", owner_user_id=user_id)
    db.add_all([User(id=user_id), ws])
    await db.commit()
    svc = NodeService(db)
    first = await svc.create(ws.id, actor_id=user_id)
    second = await svc.create(ws.id, actor_id=user_id)
    assert first.slug != second.slug
    assert HEX_RE.fullmatch(first.slug)
    assert HEX_RE.fullmatch(second.slug)


@pytest.mark.asyncio
async def test_same_slug_allowed_across_workspaces(db: AsyncSession) -> None:
    user_id = uuid.uuid4()
    ws1 = Workspace(id=uuid.uuid4(), name="W1", slug="w1", owner_user_id=user_id)
    ws2 = Workspace(id=uuid.uuid4(), name="W2", slug="w2", owner_user_id=user_id)
    db.add_all([User(id=user_id), ws1, ws2])
    await db.commit()
    svc = NodeService(db)
    first = await svc.create(ws1.id, actor_id=user_id)
    second = await svc.create(ws2.id, actor_id=user_id)
    assert first.slug == second.slug

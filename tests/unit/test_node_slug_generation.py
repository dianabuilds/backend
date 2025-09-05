import hashlib
import os
import re
import uuid

import pytest
import pytest_asyncio
import sqlalchemy as sa
from slugify import slugify
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker

os.environ.setdefault("TESTING", "true")

from app.domains.nodes.infrastructure.models.node import Node
from app.domains.nodes.infrastructure.repositories.node_repository import (
    NodeRepository,
)
from app.domains.tags.infrastructure.models.tag_models import NodeTag
from app.domains.tags.models import Tag
from app.domains.users.infrastructure.models.user import User
from app.domains.workspaces.infrastructure.models import Workspace
from app.schemas.node import NodeCreate


@pytest_asyncio.fixture()
async def db() -> AsyncSession:
    engine = create_async_engine("sqlite+aiosqlite:///:memory:")
    async with engine.begin() as conn:
        await conn.run_sync(User.__table__.create)
        await conn.run_sync(Workspace.__table__.create)
        await conn.run_sync(Tag.__table__.create)
        await conn.run_sync(NodeTag.__table__.create)
        Node.__table__.c.id.type = sa.Integer()  # type: ignore[name-defined]
        await conn.run_sync(Node.__table__.create)
    async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    async with async_session() as session:
        yield session


@pytest.mark.asyncio
async def test_create_node_generates_slug(db: AsyncSession) -> None:
    user_id = uuid.uuid4()
    ws = Workspace(id=uuid.uuid4(), name="W", slug="w", owner_user_id=user_id)
    db.add_all([User(id=user_id), ws])
    await db.commit()

    repo = NodeRepository(db)
    node = await repo.create(NodeCreate(title="Привет"), user_id, ws.id)
    expected = hashlib.sha256(slugify("Привет").encode()).hexdigest()[:16]
    assert node.slug == expected


@pytest.mark.asyncio
async def test_duplicate_titles_get_unique_slugs(db: AsyncSession) -> None:
    user_id = uuid.uuid4()
    ws = Workspace(id=uuid.uuid4(), name="W", slug="w", owner_user_id=user_id)
    db.add_all([User(id=user_id), ws])
    await db.commit()

    repo = NodeRepository(db)
    node1 = await repo.create(NodeCreate(title="Same"), user_id, ws.id)
    node2 = await repo.create(NodeCreate(title="Same"), user_id, ws.id)
    assert node1.slug != node2.slug
    assert re.fullmatch(r"[a-f0-9]{16}", node2.slug)

from __future__ import annotations

import uuid

import pytest
import pytest_asyncio
import sqlalchemy as sa
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker

from app.domains.nodes.infrastructure.models.node import Node
from app.domains.nodes.infrastructure.repositories.node_repository import NodeRepository
from app.domains.users.infrastructure.models.user import User
from app.domains.workspaces.infrastructure.models import Workspace


@pytest_asyncio.fixture()
async def db() -> AsyncSession:
    engine = create_async_engine("sqlite+aiosqlite:///:memory:")
    async with engine.begin() as conn:
        await conn.run_sync(User.__table__.create)
        await conn.run_sync(Workspace.__table__.create)
        Node.__table__.c.id.type = sa.Integer()  # type: ignore[name-defined]
        await conn.run_sync(Node.__table__.create)
    async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    async with async_session() as session:
        yield session


@pytest.mark.asyncio
async def test_repository_filters_by_account(db: AsyncSession) -> None:
    user_id = uuid.uuid4()
    ws1 = Workspace(id=1, name="W1", slug="w1", owner_user_id=user_id)
    ws2 = Workspace(id=2, name="W2", slug="w2", owner_user_id=user_id)
    n1 = Node(slug="n1", title="N1", author_id=user_id, account_id=1, created_by_user_id=user_id)
    n2 = Node(slug="n2", title="N2", author_id=user_id, account_id=2, created_by_user_id=user_id)
    db.add_all([User(id=user_id), ws1, ws2, n1, n2])
    await db.commit()

    repo = NodeRepository(db)
    assert await repo.get_by_slug("n1", 1) is not None
    assert await repo.get_by_slug("n1", 2) is None
    assert await repo.get_by_id(n1.id, 1) is not None
    assert await repo.get_by_id(n1.id, 2) is None

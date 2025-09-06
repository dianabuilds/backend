from __future__ import annotations

import uuid

import pytest
import pytest_asyncio
import sqlalchemy as sa
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker

from app.domains.nodes.infrastructure.models.node import Node
from app.domains.nodes.infrastructure.models.node_version import NodeVersion
from app.domains.nodes.infrastructure.repositories.node_repository import NodeRepository
from app.domains.tags.infrastructure.models.tag_models import NodeTag
from app.domains.tags.models import Tag
from app.schemas.node import NodeUpdate


@pytest_asyncio.fixture()
async def session() -> AsyncSession:
    engine = create_async_engine("sqlite+aiosqlite:///:memory:")
    async with engine.begin() as conn:
        accounts = sa.Table(
            "accounts",
            Node.__table__.metadata,
            sa.Column("id", sa.Integer, primary_key=True),
        )
        workspaces = sa.Table(
            "workspaces",
            Node.__table__.metadata,
            sa.Column("id", sa.Integer, primary_key=True),
        )
        await conn.run_sync(accounts.create)
        await conn.run_sync(workspaces.create)
        Tag.__table__.c.id.type = sa.Integer()
        Tag.__table__.c.workspace_id.type = sa.Integer()
        await conn.run_sync(Tag.__table__.create)
        NodeTag.__table__.c.node_id.type = sa.Integer()
        NodeTag.__table__.c.tag_id.type = sa.Integer()
        await conn.run_sync(NodeTag.__table__.create)
        Node.__table__.c.id.type = sa.Integer()
        Node.__table__.c.account_id.type = sa.Integer()
        Node.__table__.c.meta.type = sa.JSON()
        await conn.run_sync(Node.__table__.create)
        NodeVersion.__table__.c.node_id.type = sa.Integer()
        NodeVersion.__table__.c.created_by_user_id.type = sa.String()
        NodeVersion.__table__.c.meta.type = sa.JSON()
        await conn.run_sync(NodeVersion.__table__.create)
    async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    async with async_session() as s:
        yield s


@pytest.mark.asyncio
async def test_node_version_created_on_patch(session: AsyncSession) -> None:
    user_id = uuid.uuid4()
    node = Node(
        account_id=1,
        slug="n1",
        title="Old",
        meta={},
        author_id=user_id,
        is_visible=True,
        allow_feedback=True,
        is_recommendable=True,
    )
    session.add(node)
    await session.commit()
    repo = NodeRepository(session)
    await repo.update(node, NodeUpdate(title="New"), user_id)
    refreshed = await session.get(Node, node.id)
    assert refreshed.version == 2
    res = await session.execute(
        sa.select(NodeVersion).where(NodeVersion.node_id == node.id, NodeVersion.version == 2)
    )
    version = res.scalar_one()
    assert version.title == "New"
    assert str(version.created_by_user_id) == str(user_id)

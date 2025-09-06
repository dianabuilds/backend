from __future__ import annotations

import os
import uuid

import pytest
import pytest_asyncio
import sqlalchemy as sa
from fastapi import HTTPException
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker

os.environ.setdefault("TESTING", "true")

from app.domains.nodes.content_admin_router import _resolve_content_item_id
from app.domains.nodes.infrastructure.models.node import Node
from app.domains.nodes.models import NodeItem
from app.domains.users.infrastructure.models.user import User
from app.domains.workspaces.infrastructure.models import Workspace
from app.schemas.nodes_common import Status, Visibility


@pytest_asyncio.fixture()
async def db() -> AsyncSession:
    engine = create_async_engine("sqlite+aiosqlite:///:memory:")
    async with engine.begin() as conn:
        await conn.run_sync(User.__table__.create)
        await conn.run_sync(Workspace.__table__.create)
        Node.__table__.c.id.type = sa.Integer()
        Node.__table__.c.account_id.nullable = True
        await conn.run_sync(Node.__table__.create)
        NodeItem.__table__.c.id_bigint.type = sa.Integer()
        NodeItem.__table__.c.workspace_id.nullable = True
        await conn.run_sync(NodeItem.__table__.create)
    async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    async with async_session() as session:
        yield session


@pytest.mark.asyncio
async def test_node_only_creates_item(db: AsyncSession) -> None:
    user_id = uuid.uuid4()
    ws = Workspace(id=uuid.uuid4(), name="W", slug="w", owner_user_id=user_id)
    node = Node(
        id=1,
        account_id=ws.id,
        slug="n1",
        title="N1",
        author_id=user_id,
        status=Status.draft,
        visibility=Visibility.private,
        created_by_user_id=user_id,
        updated_by_user_id=user_id,
    )
    db.add_all([User(id=user_id), ws, node])
    await db.commit()

    item = await _resolve_content_item_id(db, workspace_id=ws.id, node_or_item_id=node.id)
    assert isinstance(item, NodeItem)
    assert item.node_id == node.id
    assert item.workspace_id == ws.id
    assert await db.get(NodeItem, item.id) is not None


@pytest.mark.asyncio
async def test_existing_item_by_id(db: AsyncSession) -> None:
    user_id = uuid.uuid4()
    ws = Workspace(id=uuid.uuid4(), name="W", slug="w", owner_user_id=user_id)
    node = Node(
        id=1,
        account_id=ws.id,
        slug="n1",
        title="N1",
        author_id=user_id,
        status=Status.draft,
        visibility=Visibility.private,
        created_by_user_id=user_id,
        updated_by_user_id=user_id,
    )
    item = NodeItem(
        id=2,
        node_id=node.id,
        workspace_id=ws.id,
        type="quest",
        slug="n1",
        title="N1",
        created_by_user_id=user_id,
    )
    db.add_all([User(id=user_id), ws, node, item])
    await db.commit()

    resolved = await _resolve_content_item_id(db, workspace_id=ws.id, node_or_item_id=item.id)
    assert resolved.id == item.id


@pytest.mark.asyncio
async def test_wrong_workspace_raises(db: AsyncSession) -> None:
    user_id = uuid.uuid4()
    ws1 = Workspace(id=uuid.uuid4(), name="W1", slug="w1", owner_user_id=user_id)
    ws2 = Workspace(id=uuid.uuid4(), name="W2", slug="w2", owner_user_id=user_id)
    node = Node(
        id=1,
        account_id=ws1.id,
        slug="n1",
        title="N1",
        author_id=user_id,
        status=Status.draft,
        visibility=Visibility.private,
        created_by_user_id=user_id,
        updated_by_user_id=user_id,
    )
    item = NodeItem(
        id=2,
        node_id=node.id,
        workspace_id=ws1.id,
        type="quest",
        slug="n1",
        title="N1",
        created_by_user_id=user_id,
    )
    db.add_all([User(id=user_id), ws1, ws2, node, item])
    await db.commit()

    with pytest.raises(HTTPException):
        await _resolve_content_item_id(db, workspace_id=ws2.id, node_or_item_id=item.id)


@pytest.mark.asyncio
async def test_global_node_resolves(db: AsyncSession) -> None:
    user_id = uuid.uuid4()
    ws = Workspace(id=uuid.uuid4(), name="W", slug="w", owner_user_id=user_id)
    node = Node(
        id=1,
        account_id=None,
        slug="g",
        title="G",
        author_id=user_id,
        status=Status.draft,
        visibility=Visibility.private,
        created_by_user_id=user_id,
        updated_by_user_id=user_id,
    )
    db.add_all([User(id=user_id), ws, node])
    await db.commit()

    item = await _resolve_content_item_id(db, workspace_id=ws.id, node_or_item_id=node.id)
    assert item.node_id == node.id
    assert item.workspace_id is None

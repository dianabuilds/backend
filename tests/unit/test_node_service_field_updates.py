from __future__ import annotations

import os
import sys
import uuid
from pathlib import Path

import pytest
import pytest_asyncio
import sqlalchemy as sa
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import selectinload, sessionmaker
import types

os.environ.setdefault("TESTING", "true")
sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "apps/backend"))

from app.domains.nodes.application.node_service import NodeService
module_name = "app.domains.nodes.application.editorjs_renderer"
sys.modules.setdefault(
    module_name,
    types.SimpleNamespace(
        collect_unknown_blocks=lambda _: [],
        render_html=lambda _: "",
    ),
)
from app.domains.nodes.content_admin_router import _serialize
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


async def _prepare_published(
    db: AsyncSession,
) -> tuple[Workspace, uuid.UUID, Node, NodeItem]:
    user_id = uuid.uuid4()
    ws = Workspace(id=uuid.uuid4(), name="W", slug="w", owner_user_id=user_id)
    node = Node(
        workspace_id=ws.id,
        slug="slug",
        title="t",
        author_id=user_id,
        status=Status.published,
        visibility=Visibility.public,
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
        slug="slug",
        title="t",
        created_by_user_id=user_id,
        status=Status.published,
        visibility=Visibility.public,
        version=1,
        node_id=node.id,
    )
    await db.commit()
    return ws, user_id, node, item


@pytest.mark.asyncio
async def test_update_content_resets_status(db: AsyncSession) -> None:
    ws, user_id, node, item = await _prepare_published(db)
    svc = NodeService(db)
    await svc.update(ws.id, item.id, {"content": {"x": 1}}, actor_id=user_id)
    refreshed_item = await db.get(NodeItem, item.id)
    refreshed_node = await db.get(Node, node.id)
    assert refreshed_node.content == {"x": 1}
    assert refreshed_item.status == Status.draft


@pytest.mark.asyncio
async def test_update_cover_url_resets_status(db: AsyncSession) -> None:
    ws, user_id, node, item = await _prepare_published(db)
    svc = NodeService(db)
    await svc.update(ws.id, item.id, {"cover_url": "http://x"}, actor_id=user_id)
    refreshed_node = await db.get(Node, node.id)
    refreshed_item = await db.get(NodeItem, item.id)
    assert refreshed_node.cover_url == "http://x"
    assert refreshed_item.status == Status.draft


@pytest.mark.asyncio
async def test_update_media_resets_status(db: AsyncSession) -> None:
    ws, user_id, node, item = await _prepare_published(db)
    svc = NodeService(db)
    await svc.update(ws.id, item.id, {"media": ["a", "b"]}, actor_id=user_id)
    refreshed_node = await db.get(Node, node.id)
    refreshed_item = await db.get(NodeItem, item.id)
    assert refreshed_node.media == ["a", "b"]
    assert refreshed_item.status == Status.draft


@pytest.mark.asyncio
async def test_update_tags_resets_status(db: AsyncSession) -> None:
    ws, user_id, node, item = await _prepare_published(db)
    tag_a = Tag(id=uuid.uuid4(), slug="a", name="A", workspace_id=ws.id)
    tag_b = Tag(id=uuid.uuid4(), slug="b", name="B", workspace_id=ws.id)
    db.add_all([tag_a, tag_b])
    await db.commit()
    svc = NodeService(db)
    await svc.update(ws.id, item.id, {"tags": ["a", "b"]}, actor_id=user_id)
    node_db = await db.execute(
        sa.select(Node).where(Node.id == node.id).options(selectinload(Node.tags))
    )
    node_obj = node_db.scalar_one()
    item_db = await db.execute(
        sa.select(NodeItem)
        .where(NodeItem.id == item.id)
        .options(selectinload(NodeItem.tags))
    )
    item_obj = item_db.scalar_one()
    assert sorted(t.slug for t in node_obj.tags) == ["a", "b"]
    assert sorted(t.slug for t in item_obj.tags) == ["a", "b"]
    assert item_obj.status == Status.draft


@pytest.mark.asyncio
async def test_update_creates_new_tag_and_serializes(db: AsyncSession) -> None:
    ws, user_id, node, item = await _prepare_published(db)
    svc = NodeService(db)
    await svc.update(ws.id, item.id, {"tagSlugs": ["fresh"]}, actor_id=user_id)

    res = await db.execute(
        sa.select(Tag).where(Tag.workspace_id == ws.id, Tag.slug == "fresh")
    )
    assert res.scalar_one_or_none() is not None

    node_db = await db.execute(
        sa.select(Node).where(Node.id == node.id).options(selectinload(Node.tags))
    )
    item_db = await db.execute(
        sa.select(NodeItem)
        .where(NodeItem.id == item.id)
        .options(selectinload(NodeItem.tags))
    )
    node_obj = node_db.scalar_one()
    item_obj = item_db.scalar_one()

    payload = _serialize(item_obj, node_obj)
    assert payload["tags"] == ["fresh"]
    assert [t.slug for t in node_obj.tags] == ["fresh"]
    assert [t.slug for t in item_obj.tags] == ["fresh"]


@pytest.mark.asyncio
async def test_update_multiple_fields_resets_status(db: AsyncSession) -> None:
    ws, user_id, node, item = await _prepare_published(db)
    tag_a = Tag(id=uuid.uuid4(), slug="a", name="A", workspace_id=ws.id)
    tag_b = Tag(id=uuid.uuid4(), slug="b", name="B", workspace_id=ws.id)
    db.add_all([tag_a, tag_b])
    await db.commit()
    svc = NodeService(db)
    await svc.update(
        ws.id,
        item.id,
        {
            "content": {"y": 2},
            "cover_url": "http://img",
            "media": ["m"],
            "tags": ["a", "b"],
        },
        actor_id=user_id,
    )
    node_db = await db.execute(
        sa.select(Node).where(Node.id == node.id).options(selectinload(Node.tags))
    )
    node_obj = node_db.scalar_one()
    item_db = await db.execute(
        sa.select(NodeItem)
        .where(NodeItem.id == item.id)
        .options(selectinload(NodeItem.tags))
    )
    item_obj = item_db.scalar_one()
    assert node_obj.content == {"y": 2}
    assert node_obj.cover_url == "http://img"
    assert node_obj.media == ["m"]
    assert sorted(t.slug for t in node_obj.tags) == ["a", "b"]
    assert sorted(t.slug for t in item_obj.tags) == ["a", "b"]
    assert item_obj.status == Status.draft

from __future__ import annotations

import os
import sys
import types
import uuid

import pytest
import pytest_asyncio
import sqlalchemy as sa
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import selectinload, sessionmaker

os.environ.setdefault("TESTING", "true")

from app.domains.nodes.application.node_service import NodeService

module_name = "app.domains.nodes.application.editorjs_renderer"
sys.modules.setdefault(
    module_name,
    types.SimpleNamespace(
        collect_unknown_blocks=lambda _: [],
        render_html=lambda _: "",
    ),
)
from app.domains.nodes.content_admin_router import _serialize  # noqa: E402
from app.domains.nodes.dao import NodeItemDAO  # noqa: E402
from app.domains.nodes.infrastructure.models.node import Node  # noqa: E402
from app.domains.nodes.models import NodeItem, NodePatch  # noqa: E402
from app.domains.quests.infrastructure.models.navigation_cache_models import (  # noqa: E402
    NavigationCache,
)
from app.domains.tags.infrastructure.models.tag_models import NodeTag  # noqa: E402
from app.domains.tags.models import ContentTag, Tag  # noqa: E402
from app.domains.users.infrastructure.models.user import User  # noqa: E402
from app.domains.workspaces.infrastructure.models import Workspace  # noqa: E402
from app.schemas.node import NodeOut  # noqa: E402
from app.schemas.nodes_common import Status, Visibility  # noqa: E402


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
async def test_update_coverUrl_resets_status(db: AsyncSession) -> None:
    ws, user_id, node, item = await _prepare_published(db)
    svc = NodeService(db)
    await svc.update(ws.id, item.id, {"coverUrl": "http://x"}, actor_id=user_id)
    refreshed_node = await db.get(Node, node.id)
    refreshed_item = await db.get(NodeItem, item.id)
    assert refreshed_node.coverUrl == "http://x"
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
    await svc.update(ws.id, item.id, {"tags": ["fresh"]}, actor_id=user_id)

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
    assert NodeOut.model_validate(node_obj).tags == ["fresh"]


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
            "coverUrl": "http://img",
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
    assert node_obj.coverUrl == "http://img"
    assert node_obj.media == ["m"]
    assert sorted(t.slug for t in node_obj.tags) == ["a", "b"]
    assert sorted(t.slug for t in item_obj.tags) == ["a", "b"]
    assert item_obj.status == Status.draft

from __future__ import annotations

import uuid

import pytest
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker

from app.domains.nodes.application.query_models import (
    NodeFilterSpec,
    PageRequest,
    QueryContext,
)
from app.domains.nodes.infrastructure.models.node import Node
from app.domains.nodes.infrastructure.queries.node_query_adapter import (
    NodeQueryAdapter,
)
from app.domains.nodes.models import NodeItem
from app.domains.tags.infrastructure.models.tag_models import NodeTag
from app.domains.tags.models import Tag
from app.domains.workspaces.infrastructure.models import Workspace
from app.schemas.nodes_common import Status, Visibility


@pytest.mark.asyncio
async def test_node_query_adapter_eager_loads_tags() -> None:
    engine = create_async_engine("sqlite+aiosqlite:///:memory:")
    async with engine.begin() as conn:
        await conn.run_sync(Workspace.__table__.create)
        await conn.run_sync(Tag.__table__.create)
        await conn.run_sync(Node.__table__.create)
        await conn.run_sync(NodeTag.__table__.create)
        await conn.run_sync(NodeItem.__table__.create)
    async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    async with async_session() as session:
        ws_id = uuid.uuid4()
        workspace = Workspace(id=ws_id, name="W", slug="w", owner_user_id=uuid.uuid4())
        tag = Tag(id=uuid.uuid4(), slug="t1", name="T1", workspace_id=ws_id)
        node = Node(
            id=1,
            workspace_id=ws_id,
            slug="n1",
            title="N1",
            author_id=uuid.uuid4(),
            tags=[tag],
        )
        item = NodeItem(
            id=1,
            node_id=node.id,
            workspace_id=ws_id,
            type="quest",
            slug="n1",
            title="N1",
            status=Status.published,
            visibility=Visibility.public,
            version=1,
        )
        session.add_all([workspace, tag, node, item])
        await session.commit()

        adapter = NodeQueryAdapter(session)
        spec = NodeFilterSpec(workspace_id=ws_id)
        page = PageRequest(offset=0, limit=10)
        ctx = QueryContext(user=None, is_admin=True)
        nodes = await adapter.list_nodes(spec, page, ctx)
        assert [t.slug for t in nodes[0].tags] == ["t1"]

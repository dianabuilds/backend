import uuid

import pytest
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker

from app.domains.nodes.application.node_service import NodeService
from app.domains.nodes.infrastructure.models.node import Node
from app.domains.nodes.models import NodeItem, NodePatch
from app.schemas.nodes_common import NodeType, Status, Visibility


@pytest.mark.asyncio
async def test_update_resets_published_node():
    engine = create_async_engine("sqlite+aiosqlite:///:memory:")
    async with engine.begin() as conn:
        await conn.run_sync(Node.__table__.create)
        await conn.run_sync(NodeItem.__table__.create)
        await conn.run_sync(NodePatch.__table__.create)
    async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

    async with async_session() as session:
        workspace_id = uuid.uuid4()
        creator_id = uuid.uuid4()
        node = Node(
            id=1,
            workspace_id=workspace_id,
            slug="slug-1",
            title="Title",
            author_id=creator_id,
            status=Status.draft,
            visibility=Visibility.private,
            created_by_user_id=creator_id,
            updated_by_user_id=creator_id,
        )
        session.add(node)
        await session.commit()

        item = NodeItem(
            id=uuid.uuid4(),
            node_id=node.id,
            workspace_id=workspace_id,
            type=NodeType.quest.value,
            slug="slug-1",
            title="Title",
            status=Status.published,
            created_by_user_id=creator_id,
        )
        session.add(item)
        await session.commit()

        svc = NodeService(session)
        await svc.update(
            item.workspace_id,
            item.id,
            {"title": "New title"},
            actor_id=item.created_by_user_id,
        )

        refreshed = await session.get(NodeItem, item.id)
        assert refreshed.status == Status.draft

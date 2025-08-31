import uuid
import sqlalchemy as sa
import pytest
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker, relationship

from app.domains.nodes.models import NodeItem, NodePatch
from app.domains.nodes.application.node_service import NodeService
from app.domains.nodes.infrastructure.models.node import Node
from app.domains.tags.models import Tag  # noqa: F401
from app.domains.tags.infrastructure.models.tag_models import NodeTag  # noqa: F401
from app.schemas.nodes_common import NodeType, Status, Visibility

# Ensure Node model has a tags relationship for test mappings
Node.tags = relationship("Tag", secondary="node_tags", back_populates="nodes")


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
            NodeType.quest,
            item.id,
            {"title": "New title"},
            actor_id=item.created_by_user_id,
        )

        refreshed = await session.get(NodeItem, item.id)
        assert refreshed.status == Status.draft

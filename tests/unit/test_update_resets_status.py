import uuid
import sqlalchemy as sa
import pytest
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker

from app.domains.nodes.models import NodeItem, NodePatch
from app.domains.nodes.application.node_service import NodeService
from app.schemas.nodes_common import NodeType, Status


@pytest.mark.asyncio
async def test_update_resets_published_node():
    engine = create_async_engine("sqlite+aiosqlite:///:memory:")
    async with engine.begin() as conn:
        await conn.run_sync(NodeItem.__table__.create)
        await conn.run_sync(NodePatch.__table__.create)
    async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

    async with async_session() as session:
        node = NodeItem(
            id=uuid.uuid4(),
            workspace_id=uuid.uuid4(),
            type=NodeType.quest.value,
            slug="slug-1",
            title="Title",
            status=Status.published,
            created_by_user_id=uuid.uuid4(),
        )
        session.add(node)
        await session.commit()

        svc = NodeService(session)
        await svc.update(
            node.workspace_id,
            NodeType.quest,
            node.id,
            {"title": "New title"},
            actor_id=node.created_by_user_id,
        )

        refreshed = await session.get(NodeItem, node.id)
        assert refreshed.status == Status.draft

        res = await session.execute(sa.select(NodePatch))
        patches = res.scalars().all()
        assert any(p.data.get("action") == "status_reset" for p in patches)

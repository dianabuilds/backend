import uuid

import pytest
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker

from app.domains.nodes.models import NodeItem
from app.schemas.nodes_common import NodeType, Status
from app.validation import run_validators


@pytest.mark.asyncio
async def test_run_validators_noop_for_quest():
    engine = create_async_engine("sqlite+aiosqlite:///:memory:")
    async with engine.begin() as conn:
        await conn.run_sync(NodeItem.__table__.create)
    async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

    async with async_session() as session:
        node = NodeItem(
            id=uuid.uuid4(),
            workspace_id=uuid.uuid4(),
            type=NodeType.quest.value,
            slug="slug",
            title="Title",
            status=Status.draft,
            created_by_user_id=uuid.uuid4(),
        )
        session.add(node)
        await session.commit()

        report = await run_validators(NodeType.quest.value, node.id, session)
        assert report.errors == 0
        assert report.warnings == 0
        assert report.items == []

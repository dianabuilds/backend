import uuid
from datetime import datetime

import pytest
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker

from app.domains.quests.application.quest_graph_service import QuestGraphService
from app.domains.quests.infrastructure.models.navigation_cache_models import (
    NavigationCache,
)
from app.domains.quests.infrastructure.models.quest_version_models import (
    QuestGraphEdge,
    QuestGraphNode,
    QuestVersion,
)
from app.domains.quests.schemas import QuestStep, QuestTransition


@pytest.mark.asyncio
async def test_save_graph_generates_navigation_cache() -> None:
    engine = create_async_engine("sqlite+aiosqlite:///:memory:")
    async with engine.begin() as conn:
        await conn.run_sync(QuestVersion.__table__.create)
        await conn.run_sync(QuestGraphNode.__table__.create)
        await conn.run_sync(QuestGraphEdge.__table__.create)
        await conn.run_sync(NavigationCache.__table__.create)
    async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

    svc = QuestGraphService()
    async with async_session() as session:
        version = QuestVersion(
            id=uuid.uuid4(),
            quest_id=uuid.uuid4(),
            number=1,
            status="draft",
            created_at=datetime.utcnow(),
        )
        session.add(version)
        await session.commit()
        steps = [
            QuestStep(key="start", title="Start", type="start", content={}, rewards=None),
            QuestStep(key="end", title="End", type="end", content={}, rewards=None),
        ]
        transitions = [
            QuestTransition(from_node_key="start", to_node_key="end", label="go", condition=None)
        ]
        await svc.save_graph(session, version.id, steps, transitions)
        await session.commit()
        res = await session.execute(
            select(NavigationCache).where(NavigationCache.node_slug == "start")
        )
        row = res.scalar_one()
        assert row.navigation["transitions"][0]["slug"] == "end"

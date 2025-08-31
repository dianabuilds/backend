import os
import sys
import types
import uuid

import pytest
from sqlalchemy import Column
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import declarative_base, sessionmaker

from app.core.db.adapters import UUID

# Provide a minimal ``app.models`` package with Base to satisfy model imports
Base = declarative_base()
models_pkg = types.ModuleType("app.models")
models_pkg.Base = Base
models_pkg.__path__ = [
    os.path.join(os.getcwd(), "apps/backend/app/models")
]  # mark as package
sys.modules.setdefault("app.models", models_pkg)

from app.domains.quests.services import QuestStepService  # noqa: E402
from app.models.quests import QuestStep, QuestStepTransition  # noqa: E402


class Quest(Base):  # Minimal quest model for tests
    __tablename__ = "quests"

    id = Column(UUID(), primary_key=True, default=uuid.uuid4)


@pytest.mark.asyncio
async def test_step_crud_and_order() -> None:
    engine = create_async_engine("sqlite+aiosqlite:///:memory:")
    async with engine.begin() as conn:
        await conn.run_sync(Quest.__table__.create)
        await conn.run_sync(QuestStep.__table__.create)
        await conn.run_sync(QuestStepTransition.__table__.create)
    async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

    svc = QuestStepService()
    async with async_session() as session:
        quest = Quest()
        session.add(quest)
        await session.commit()

        s1 = await svc.create_step(
            session, quest.id, key="s1", title="Start", type="start"
        )
        s2 = await svc.create_step(session, quest.id, key="s2", title="Second")
        assert s1.order == 1
        assert s2.order == 2

        s2 = await svc.update_step(session, s2.id, title="Updated")
        assert s2.title == "Updated"

        await svc.delete_step(session, s1.id)
        s3 = await svc.create_step(session, quest.id, key="s3", title="Third")
        assert s3.order == 3

        await svc.delete_step(session, s2.id)
        await svc.delete_step(session, s3.id)
        assert await session.get(QuestStep, s1.id) is None


@pytest.mark.asyncio
async def test_start_step_unique() -> None:
    engine = create_async_engine("sqlite+aiosqlite:///:memory:")
    async with engine.begin() as conn:
        await conn.run_sync(Quest.__table__.create)
        await conn.run_sync(QuestStep.__table__.create)
        await conn.run_sync(QuestStepTransition.__table__.create)
    async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

    svc = QuestStepService()
    async with async_session() as session:
        quest = Quest()
        session.add(quest)
        await session.commit()

        await svc.create_step(session, quest.id, key="s1", title="Start", type="start")
        with pytest.raises(ValueError):
            await svc.create_step(
                session, quest.id, key="s2", title="Another", type="start"
            )


@pytest.mark.asyncio
async def test_transition_requires_same_quest() -> None:
    engine = create_async_engine("sqlite+aiosqlite:///:memory:")
    async with engine.begin() as conn:
        await conn.run_sync(Quest.__table__.create)
        await conn.run_sync(QuestStep.__table__.create)
        await conn.run_sync(QuestStepTransition.__table__.create)
    async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

    svc = QuestStepService()
    async with async_session() as session:
        q1 = Quest()
        q2 = Quest()
        session.add_all([q1, q2])
        await session.commit()

        s1 = await svc.create_step(session, q1.id, key="s1", title="S1")
        s2 = await svc.create_step(session, q2.id, key="t1", title="S2")
        with pytest.raises(ValueError):
            await svc.create_transition(
                session,
                q1.id,
                from_step_id=s1.id,
                to_step_id=s2.id,
            )
        s3 = await svc.create_step(session, q1.id, key="s3", title="S3")
        tr = await svc.create_transition(
            session,
            q1.id,
            from_step_id=s1.id,
            to_step_id=s3.id,
        )
        await svc.delete_transition(session, tr.id)
        assert await session.get(QuestStepTransition, tr.id) is None


@pytest.mark.asyncio
async def test_transition_from_end_step_forbidden() -> None:
    engine = create_async_engine("sqlite+aiosqlite:///:memory:")
    async with engine.begin() as conn:
        await conn.run_sync(Quest.__table__.create)
        await conn.run_sync(QuestStep.__table__.create)
        await conn.run_sync(QuestStepTransition.__table__.create)
    async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

    svc = QuestStepService()
    async with async_session() as session:
        quest = Quest()
        session.add(quest)
        await session.commit()

        end_step = await svc.create_step(
            session, quest.id, key="end", title="End", type="end"
        )
        other_step = await svc.create_step(session, quest.id, key="next", title="Next")
        with pytest.raises(ValueError):
            await svc.create_transition(
                session,
                quest.id,
                from_step_id=end_step.id,
                to_step_id=other_step.id,
            )


@pytest.mark.asyncio
async def test_get_graph_returns_steps_and_transitions() -> None:
    engine = create_async_engine("sqlite+aiosqlite:///:memory:")
    async with engine.begin() as conn:
        await conn.run_sync(Quest.__table__.create)
        await conn.run_sync(QuestStep.__table__.create)
        await conn.run_sync(QuestStepTransition.__table__.create)
    async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

    svc = QuestStepService()
    async with async_session() as session:
        quest = Quest()
        session.add(quest)
        await session.commit()

        s1 = await svc.create_step(session, quest.id, key="s1", title="Start")
        s2 = await svc.create_step(session, quest.id, key="s2", title="End")
        await svc.create_transition(
            session, quest.id, from_step_id=s1.id, to_step_id=s2.id
        )
        steps, transitions = await svc.get_graph(session, quest.id)
        assert len(steps) == 2
        assert len(transitions) == 1

import asyncio
import importlib
import sys
import uuid

import sqlalchemy as sa
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker

app_module = importlib.import_module("apps.backend.app")
sys.modules.setdefault("app", app_module)

from app.core.preview import PreviewContext  # noqa: E402
from app.domains.achievements.application.achievements_service import (  # noqa: E402
    AchievementsService,
)
from app.domains.achievements.infrastructure.models.achievement_models import (  # noqa: E402
    Achievement,
    UserAchievement,
)
from app.domains.achievements.infrastructure.repositories.achievements_repository import (  # noqa: E402,E501
    AchievementsRepository,
)
from app.domains.nodes.infrastructure.models.node import Node  # noqa: E402
from app.domains.notifications.infrastructure.models.notification_models import (  # noqa: E402
    Notification,
)
from app.domains.users.infrastructure.models.user import User  # noqa: E402
from app.domains.workspaces.infrastructure.models import Workspace  # noqa: E402
from app.models.event_counter import UserEventCounter  # noqa: E402


def test_process_event_isolated_by_workspace() -> None:
    async def _run() -> None:
        engine = create_async_engine("sqlite+aiosqlite:///:memory:")
        async with engine.begin() as conn:
            await conn.run_sync(User.__table__.create)
            await conn.run_sync(Workspace.__table__.create)
            await conn.run_sync(Achievement.__table__.create)
            await conn.run_sync(UserAchievement.__table__.create)
            await conn.run_sync(Notification.__table__.create)
            await conn.run_sync(UserEventCounter.__table__.create)
        async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

        async with async_session() as session:
            user = User(id=uuid.uuid4())
            w1 = Workspace(id=uuid.uuid4(), name="W1", slug="w1", owner_user_id=user.id)
            w2 = Workspace(id=uuid.uuid4(), name="W2", slug="w2", owner_user_id=user.id)
            ach1 = Achievement(
                workspace_id=w1.id,
                code="a1",
                title="A1",
                condition={"type": "event_count", "event": "foo", "count": 1},
                created_by_user_id=user.id,
            )
            ach2 = Achievement(
                workspace_id=w2.id,
                code="a2",
                title="A2",
                condition={"type": "event_count", "event": "foo", "count": 1},
                created_by_user_id=user.id,
            )
            session.add_all([user, w1, w2, ach1, ach2])
            await session.commit()

            from contextlib import asynccontextmanager

            from app.domains.system.events.handlers import handlers as event_handlers

            @asynccontextmanager
            async def _db_session() -> AsyncSession:
                yield session

            event_handlers.db_session = _db_session

            unlocked1 = await AchievementsService.process_event(
                session, w1.id, user.id, "foo", preview=PreviewContext()
            )
            assert [u.id for u in unlocked1] == [ach1.id]

            unlocked2 = await AchievementsService.process_event(
                session, w2.id, user.id, "foo", preview=PreviewContext()
            )
            assert [u.id for u in unlocked2] == [ach2.id]

            c1 = await session.get(
                UserEventCounter,
                {"workspace_id": w1.id, "user_id": user.id, "event": "foo"},
            )
            c2 = await session.get(
                UserEventCounter,
                {"workspace_id": w2.id, "user_id": user.id, "event": "foo"},
            )
            assert c1.count == 1
            assert c2.count == 1

            notes = (await session.execute(Notification.__table__.select())).fetchall()
            assert len(notes) == 2

    asyncio.run(_run())


def test_repository_isolated_by_workspace() -> None:
    async def _run() -> None:
        engine = create_async_engine("sqlite+aiosqlite:///:memory:")
        async with engine.begin() as conn:
            await conn.run_sync(User.__table__.create)
            await conn.run_sync(Workspace.__table__.create)
            await conn.run_sync(Achievement.__table__.create)
            await conn.run_sync(UserAchievement.__table__.create)
            Node.__table__.c.id.type = sa.Integer()
            await conn.run_sync(Node.__table__.create)
            await conn.run_sync(UserEventCounter.__table__.create)
        async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

        async with async_session() as session:
            user = User(id=uuid.uuid4())
            w1 = Workspace(id=uuid.uuid4(), name="W1", slug="w1", owner_user_id=user.id)
            w2 = Workspace(id=uuid.uuid4(), name="W2", slug="w2", owner_user_id=user.id)
            n1 = Node(
                workspace_id=w1.id,
                slug="n1",
                content={},
                author_id=user.id,
                views=10,
            )
            n2 = Node(
                workspace_id=w1.id,
                slug="n2",
                content={},
                author_id=user.id,
                views=5,
            )
            n3 = Node(
                workspace_id=w2.id,
                slug="n3",
                content={},
                author_id=user.id,
                views=20,
            )
            session.add_all([user, w1, w2, n1, n2, n3])
            await session.commit()

            repo = AchievementsRepository(session)
            await repo.increment_counter(user.id, "evt", w1.id)
            await repo.increment_counter(user.id, "evt", w1.id)
            await repo.increment_counter(user.id, "evt", w2.id)

            cnt_w1 = await repo.get_counter(user.id, "evt", w1.id)
            cnt_w2 = await repo.get_counter(user.id, "evt", w2.id)
            assert cnt_w1 == 2
            assert cnt_w2 == 1

            nodes_w1 = await repo.count_nodes_by_author(user.id, w1.id)
            nodes_w2 = await repo.count_nodes_by_author(user.id, w2.id)
            assert nodes_w1 == 2
            assert nodes_w2 == 1

            views_w1 = await repo.sum_views_by_author(user.id, w1.id)
            views_w2 = await repo.sum_views_by_author(user.id, w2.id)
            assert views_w1 == 15
            assert views_w2 == 20

    asyncio.run(_run())

import asyncio
import importlib
import sys
import uuid
from pathlib import Path

from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
app_module = importlib.import_module("apps.backend.app")
sys.modules.setdefault("app", app_module)

from app.core.db.base import Base  # noqa: E402
from app.domains.achievements.application.achievements_service import (  # noqa: E402
    AchievementsService,
)
from app.domains.achievements.infrastructure.models.achievement_models import (  # noqa: E402
    Achievement,
)
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
            await conn.run_sync(Base.metadata.create_all)
        async_session = sessionmaker(
            engine, class_=AsyncSession, expire_on_commit=False
        )

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

            unlocked1 = await AchievementsService.process_event(
                session, w1.id, user.id, "foo"
            )
            assert [u.id for u in unlocked1] == [ach1.id]

            unlocked2 = await AchievementsService.process_event(
                session, w2.id, user.id, "foo"
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

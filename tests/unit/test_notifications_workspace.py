import importlib
import sys
import uuid

from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker

app_module = importlib.import_module("apps.backend.app")
sys.modules.setdefault("app", app_module)

from app.core.db.base import Base  # noqa: E402
from app.domains.notifications.api.routers import list_notifications  # noqa: E402
from app.domains.notifications.infrastructure.models.notification_models import (  # noqa: E402, E501
    Notification,  # noqa: E402
)
from app.domains.users.infrastructure.models.user import User  # noqa: E402
from app.domains.workspaces.infrastructure.models import Workspace  # noqa: E402


def test_list_notifications_scoped_by_workspace() -> None:
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
            n1 = Notification(
                workspace_id=w1.id, user_id=user.id, title="T1", message="M1"
            )
            n2 = Notification(
                workspace_id=w2.id, user_id=user.id, title="T2", message="M2"
            )
            session.add_all([user, w1, w2, n1, n2])
            await session.commit()

            res1 = await list_notifications(
                workspace_id=w1.id, current_user=user, db=session
            )
            res2 = await list_notifications(
                workspace_id=w2.id, current_user=user, db=session
            )
            assert [r.workspace_id for r in res1] == [w1.id]
            assert [r.workspace_id for r in res2] == [w2.id]

    import asyncio

    asyncio.run(_run())

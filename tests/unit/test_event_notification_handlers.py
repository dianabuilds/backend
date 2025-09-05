from __future__ import annotations

import importlib
import sys
import uuid
from contextlib import asynccontextmanager

import pytest
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker

app_module = importlib.import_module("apps.backend.app")
sys.modules.setdefault("app", app_module)

from app.domains.notifications.infrastructure.models.notification_models import (  # noqa: E402
    Notification,
)
from app.domains.system.events import (  # noqa: E402
    AchievementUnlocked,
    EventBus,
    PurchaseCompleted,
)
from app.domains.system.events.handlers import handlers  # noqa: E402
from app.domains.users.infrastructure.models.user import User  # noqa: E402
from app.domains.workspaces.infrastructure.models import Workspace  # noqa: E402
from app.schemas.notification import NotificationType  # noqa: E402


@pytest.mark.asyncio
async def test_achievement_event_creates_notification(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    engine = create_async_engine("sqlite+aiosqlite:///:memory:")
    async with engine.begin() as conn:
        await conn.run_sync(User.__table__.create)
        await conn.run_sync(Workspace.__table__.create)
        await conn.run_sync(Notification.__table__.create)
    async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    async with async_session() as session:
        user = User(id=uuid.uuid4())
        ws = Workspace(id=uuid.uuid4(), name="w", slug="w", owner_user_id=user.id)
        session.add_all([user, ws])
        await session.commit()

        @asynccontextmanager
        async def _db_session() -> AsyncSession:
            yield session

        monkeypatch.setattr(handlers, "db_session", _db_session)
        bus = EventBus()
        bus.subscribe(AchievementUnlocked, handlers.handle_achievement_unlocked)
        await bus.publish(
            AchievementUnlocked(
                achievement_id=uuid.uuid4(),
                user_id=user.id,
                workspace_id=ws.id,
                title="Achieved",
                message="Achieved",
            )
        )
        res = await session.execute(select(Notification))
        notif = res.scalar_one()
        assert notif.title == "Achieved"
        assert notif.type == NotificationType.achievement


@pytest.mark.asyncio
async def test_purchase_event_creates_notification(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    engine = create_async_engine("sqlite+aiosqlite:///:memory:")
    async with engine.begin() as conn:
        await conn.run_sync(User.__table__.create)
        await conn.run_sync(Notification.__table__.create)
    async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    async with async_session() as session:
        user = User(id=uuid.uuid4())
        session.add(user)
        await session.commit()

        @asynccontextmanager
        async def _db_session() -> AsyncSession:
            yield session

        monkeypatch.setattr(handlers, "db_session", _db_session)
        bus = EventBus()
        bus.subscribe(PurchaseCompleted, handlers.handle_purchase_completed)
        await bus.publish(
            PurchaseCompleted(
                user_id=user.id,
                workspace_id=None,
                title="Bought",
                message="Bought",
            )
        )
        res = await session.execute(select(Notification))
        notif = res.scalar_one()
        assert notif.title == "Bought"
        assert notif.type == NotificationType.purchase

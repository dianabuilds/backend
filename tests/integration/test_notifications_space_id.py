from __future__ import annotations

import importlib
import sys
import types
import uuid
from enum import Enum

import pytest
import pytest_asyncio
import sqlalchemy as sa
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker

from app.core.config import settings

workspace_limits_stub = types.ModuleType("app.domains.workspaces.limits")


def workspace_limit(*_args, **_kwargs):
    def decorator(func):
        return func

    return decorator


workspace_limits_stub.workspace_limit = workspace_limit
sys.modules["app.domains.workspaces.limits"] = workspace_limits_stub

notification_stub = types.ModuleType("app.schemas.notification")


class NotificationPlacement(str, Enum):
    inbox = "inbox"


class NotificationType(str, Enum):
    system = "system"


class NotificationOut:  # minimal stub
    pass


notification_stub.NotificationPlacement = NotificationPlacement
notification_stub.NotificationType = NotificationType
notification_stub.NotificationOut = NotificationOut
sys.modules["app.schemas.notification"] = notification_stub

NotifyService = importlib.import_module(
    "app.domains.notifications.application.notify_service"
).NotifyService
INotificationPusher = importlib.import_module(
    "app.domains.notifications.application.ports.pusher"
).INotificationPusher
Notification = importlib.import_module(
    "app.domains.notifications.infrastructure.models.notification_models"
).Notification
NotificationRepository = importlib.import_module(
    "app.domains.notifications.infrastructure.repositories.notification_repository"
).NotificationRepository


class DummyPusher(INotificationPusher):
    async def send(self, user_id, data):
        return None


@pytest_asyncio.fixture()
async def session() -> tuple[AsyncSession, sa.Table, sa.Table]:
    engine = create_async_engine("sqlite+aiosqlite:///:memory:")
    metadata = Notification.__table__.metadata
    if "workspaces" in metadata.tables:
        workspaces = metadata.tables["workspaces"]
    else:
        workspaces = sa.Table("workspaces", metadata, sa.Column("id", sa.String, primary_key=True))
    if "users" in metadata.tables:
        users = metadata.tables["users"]
    else:
        users = sa.Table("users", metadata, sa.Column("id", sa.String, primary_key=True))
    async with engine.begin() as conn:
        await conn.run_sync(metadata.create_all)
    async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    async with async_session() as s:
        yield s, workspaces, users


@pytest.mark.asyncio
async def test_notifications_space_id_flag_disabled(
    session: tuple[AsyncSession, sa.Table, sa.Table]
):
    db, workspaces, users = session
    settings.spaces_enforced = False
    repo = NotificationRepository(db)
    svc = NotifyService(repo, DummyPusher())
    ws_id = uuid.uuid4()
    user_id = uuid.uuid4()
    await db.execute(sa.insert(workspaces).values(id=str(ws_id)))
    await db.execute(sa.insert(users).values(id=str(user_id)))
    await db.commit()
    await svc.create_notification(
        workspace_id=ws_id,
        user_id=user_id,
        title="Hello",
        message="World",
        type="system",
    )
    res = await db.execute(select(Notification).where(Notification.workspace_id == ws_id))
    notif = res.scalar_one()
    assert notif.title == "Hello"


@pytest.mark.asyncio
async def test_notifications_space_id_flag_enabled(
    session: tuple[AsyncSession, sa.Table, sa.Table]
):
    db, workspaces, users = session
    settings.spaces_enforced = True
    repo = NotificationRepository(db)
    svc = NotifyService(repo, DummyPusher())
    ws_id = uuid.uuid4()
    other_ws = uuid.uuid4()
    user_id = uuid.uuid4()
    await db.execute(sa.insert(workspaces).values(id=str(ws_id)))
    await db.execute(sa.insert(workspaces).values(id=str(other_ws)))
    await db.execute(sa.insert(users).values(id=str(user_id)))
    await db.commit()
    with pytest.raises(ValueError):
        await svc.create_notification(
            workspace_id=ws_id,
            user_id=user_id,
            title="Fail",
            message="",
            type="system",
        )
    await svc.create_notification(
        space_id=ws_id,
        user_id=user_id,
        title="Hello",
        message="World",
        type="system",
    )
    res = await db.execute(select(Notification).where(Notification.workspace_id == ws_id))
    notif = res.scalar_one()
    assert notif.title == "Hello"
    res2 = await db.execute(select(Notification).where(Notification.workspace_id == other_ws))
    assert res2.scalar_one_or_none() is None

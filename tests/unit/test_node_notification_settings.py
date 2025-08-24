import uuid
import importlib
import sys
from pathlib import Path
import os

import pytest
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
os.environ["TESTING"] = "True"
sys.modules.setdefault("app", importlib.import_module("apps.backend.app"))

from app.domains.notifications.infrastructure.models.notification_settings_models import (
    NodeNotificationSetting,
)
from app.domains.notifications.infrastructure.repositories.settings_repository import (
    NodeNotificationSettingsRepository,
)


@pytest.mark.asyncio
async def test_upsert_and_get_notification_settings() -> None:
    engine = create_async_engine("sqlite+aiosqlite:///:memory:")
    async with engine.begin() as conn:
        await conn.run_sync(NodeNotificationSetting.__table__.create)
    async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

    async with async_session() as session:
        repo = NodeNotificationSettingsRepository(session)
        user_id = uuid.uuid4()
        node_id = uuid.uuid4()

        setting = await repo.upsert(user_id, node_id, False)
        assert setting.enabled is False

        fetched = await repo.get(user_id, node_id)
        assert fetched is not None
        assert fetched.enabled is False

        await repo.upsert(user_id, node_id, True)
        fetched = await repo.get(user_id, node_id)
        assert fetched is not None
        assert fetched.enabled is True

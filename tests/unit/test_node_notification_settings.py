import uuid
import importlib
import sys
from pathlib import Path
import os

import pytest
import sqlalchemy as sa
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
    metadata = NodeNotificationSetting.__table__.metadata
    nodes = sa.Table(
        "nodes",
        metadata,
        sa.Column("id", sa.BigInteger, primary_key=True),
        sa.Column("alt_id", sa.String, unique=True, nullable=False),
    )
    node_alt_id = uuid.uuid4()
    async with engine.begin() as conn:
        await conn.run_sync(metadata.create_all)
        await conn.execute(nodes.insert().values(id=1, alt_id=str(node_alt_id)))
    async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

    async with async_session() as session:
        repo = NodeNotificationSettingsRepository(session)
        user_id = uuid.uuid4()
        setting = await repo.upsert(user_id, node_alt_id, False)
        assert setting.enabled is False

        fetched = await repo.get(user_id, node_alt_id)
        assert fetched is not None
        assert fetched.enabled is False

        # Upsert using numeric id should also work
        await repo.upsert(user_id, 1, True)
        fetched = await repo.get(user_id, 1)
        assert fetched is not None
        assert fetched.enabled is True

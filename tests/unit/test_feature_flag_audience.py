import importlib
import sys
from types import SimpleNamespace

import pytest
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker

app_module = importlib.import_module("apps.backend.app")
sys.modules.setdefault("app", app_module)
domains_module = importlib.import_module("apps.backend.app.domains")
sys.modules.setdefault("app.domains", domains_module)

from app.domains.admin.application.feature_flag_service import (  # noqa: E402
    get_effective_flags,
)
from app.domains.admin.infrastructure.models.feature_flag import (  # noqa: E402
    FeatureFlag,
)


@pytest.mark.asyncio
async def test_premium_audience_flag():
    engine = create_async_engine("sqlite+aiosqlite:///:memory:")
    async with engine.begin() as conn:
        await conn.run_sync(FeatureFlag.__table__.create)
    async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

    async with async_session() as session:
        session.add(FeatureFlag(key="foo", value=True, audience="premium"))
        await session.commit()

        premium_user = SimpleNamespace(is_premium=True)
        flags = await get_effective_flags(session, None, premium_user)
        assert "foo" in flags

        regular_user = SimpleNamespace(is_premium=False)
        flags = await get_effective_flags(session, None, regular_user)
        assert "foo" not in flags

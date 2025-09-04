from __future__ import annotations

import importlib
import sys
from pathlib import Path

import pytest
import pytest_asyncio
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker

# Ensure "app" package resolves correctly
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
app_module = importlib.import_module("apps.backend.app")
sys.modules.setdefault("app", app_module)

from app.core.feature_flags import ensure_known_flags, set_flag  # noqa: E402
from app.domains.admin.infrastructure.models.feature_flag import (  # noqa: E402
    FeatureFlag,
)


@pytest_asyncio.fixture()
async def db_session() -> AsyncSession:
    engine = create_async_engine("sqlite+aiosqlite:///:memory:")
    async with engine.begin() as conn:
        await conn.run_sync(FeatureFlag.__table__.create)
    async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    async with async_session() as session:
        yield session


@pytest.mark.asyncio
async def test_set_flag_unknown_key(db_session: AsyncSession) -> None:
    with pytest.raises(ValueError):
        await set_flag(db_session, "unknown.flag")


@pytest.mark.asyncio
async def test_ensure_known_flags_unknown_key(db_session: AsyncSession) -> None:
    db_session.add(FeatureFlag(key="unknown.flag", value=False))
    await db_session.commit()
    with pytest.raises(ValueError):
        await ensure_known_flags(db_session)

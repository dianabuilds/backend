from __future__ import annotations

import importlib
import sys
from types import SimpleNamespace

import pytest
import pytest_asyncio
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker

# Ensure "app" package resolves correctly
app_module = importlib.import_module("apps.backend.app")
sys.modules.setdefault("app", app_module)
user_module = sys.modules.get("apps.backend.app.domains.users.infrastructure.models.user")
if user_module is None:
    user_module = importlib.import_module(
        "apps.backend.app.domains.users.infrastructure.models.user"
    )
sys.modules.setdefault("app.domains.users.infrastructure.models.user", user_module)
domains_module = importlib.import_module("apps.backend.app.domains")
sys.modules.setdefault("app.domains", domains_module)

from app.providers.db.base import Base  # noqa: E402

Base.metadata.clear()

from app.domains.admin.application.feature_flag_service import (  # noqa: E402
    FeatureFlagKey,
    ensure_known_flags,
    get_effective_flags,
    invalidate_cache,
    set_flag,
)
from app.domains.admin.infrastructure.models.feature_flag import (  # noqa: E402
    FeatureFlag,
)
from app.domains.users.infrastructure.models.user import User  # noqa: E402, F401


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


@pytest.mark.asyncio
async def test_referrals_program_toggle(db_session: AsyncSession) -> None:
    await ensure_known_flags(db_session)
    await db_session.commit()
    flags = await get_effective_flags(db_session, None, None)
    assert FeatureFlagKey.REFERRALS_PROGRAM.value not in flags

    await set_flag(db_session, FeatureFlagKey.REFERRALS_PROGRAM, True)
    await db_session.commit()
    flags = await get_effective_flags(db_session, None, None)
    assert FeatureFlagKey.REFERRALS_PROGRAM.value in flags

    await set_flag(db_session, FeatureFlagKey.REFERRALS_PROGRAM, False)
    await db_session.commit()
    flags = await get_effective_flags(db_session, None, None)
    assert FeatureFlagKey.REFERRALS_PROGRAM.value not in flags
    invalidate_cache()


NEW_FLAGS = [
    FeatureFlagKey.CONTENT_SCHEDULING,
    FeatureFlagKey.ADMIN_BETA_DASHBOARD,
    FeatureFlagKey.NOTIFICATIONS_DIGEST,
    FeatureFlagKey.PREMIUM_GIFTING,
    FeatureFlagKey.NODE_NAVIGATION_V2,
    FeatureFlagKey.WEIGHTED_MANUAL_TRANSITIONS,
    FeatureFlagKey.FALLBACK_POLICY,
    FeatureFlagKey.ADMIN_OVERRIDE,
    FeatureFlagKey.NAV_CACHE_V2,
]


@pytest.mark.asyncio
async def test_new_flags_default_off(db_session: AsyncSession) -> None:
    await ensure_known_flags(db_session)
    await db_session.commit()
    flags = await get_effective_flags(db_session, None, None)
    for flag in NEW_FLAGS:
        assert flag.value not in flags
    invalidate_cache()


@pytest.mark.asyncio
async def test_ai_quest_wizard_premium_audience(db_session: AsyncSession) -> None:
    await ensure_known_flags(db_session)
    await db_session.commit()
    flag = await db_session.get(FeatureFlag, FeatureFlagKey.AI_QUEST_WIZARD.value)
    assert flag is not None
    assert flag.audience == "premium"

    await set_flag(db_session, FeatureFlagKey.AI_QUEST_WIZARD, True)
    await db_session.commit()
    premium_user = SimpleNamespace(is_premium=True)
    regular_user = SimpleNamespace(is_premium=False)
    flags = await get_effective_flags(db_session, None, premium_user)
    assert FeatureFlagKey.AI_QUEST_WIZARD.value in flags
    flags = await get_effective_flags(db_session, None, regular_user)
    assert FeatureFlagKey.AI_QUEST_WIZARD.value not in flags
    invalidate_cache()

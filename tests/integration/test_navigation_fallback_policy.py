from __future__ import annotations

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
    FeatureFlagKey,
    invalidate_cache,
    set_flag,
)
from app.domains.admin.infrastructure.models.feature_flag import FeatureFlag  # noqa: E402
from app.domains.navigation.application.navigation_service import NavigationService  # noqa: E402
from app.domains.navigation.application.providers import TransitionProvider  # noqa: E402


class EmptyProvider(TransitionProvider):
    async def get_transitions(self, db, node, user, account_id, preview=None):  # type: ignore[override]
        return []


@pytest.mark.asyncio
async def test_fallback_policy_returns_start(monkeypatch):
    engine = create_async_engine("sqlite+aiosqlite:///:memory:")
    async with engine.begin() as conn:
        await conn.run_sync(FeatureFlag.__table__.create)
    async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

    async with async_session() as session:
        await set_flag(session, FeatureFlagKey.FALLBACK_POLICY, True)
        await session.commit()
        invalidate_cache()

        import app.domains.navigation.application.navigation_service as nav_module

        for name in (
            "ManualTransitionsProvider",
            "EchoProvider",
            "CompassProvider",
            "RandomProvider",
        ):
            monkeypatch.setattr(nav_module, name, lambda *a, **k: EmptyProvider())

        svc = NavigationService()
        start = SimpleNamespace(slug="start", workspace_id="ws1", account_id=1)
        result = await svc.get_next(session, start, None)
        assert result.next.slug == "fallback"
        assert result.metrics.get("fallback_used")
        assert result.trace[-1].policy == "fallback"

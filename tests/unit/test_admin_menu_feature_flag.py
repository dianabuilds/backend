from __future__ import annotations

import importlib
import json
import sys
from types import SimpleNamespace

import pytest
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker
from starlette.requests import Request

app_module = importlib.import_module("apps.backend.app")
sys.modules.setdefault("app", app_module)

domains_module = importlib.import_module("apps.backend.app.domains")
sys.modules.setdefault("app.domains", domains_module)

from app.domains.admin.api.routers import get_admin_menu  # noqa: E402
from app.domains.admin.application.feature_flag_service import (  # noqa: E402
    FeatureFlagKey,
    ensure_known_flags,
    invalidate_cache,
    set_flag,
)
from app.domains.admin.application.menu_service import (  # noqa: E402
    invalidate_menu_cache,
)
from app.domains.admin.infrastructure.models.feature_flag import (  # noqa: E402
    FeatureFlag,
)


@pytest.mark.asyncio
async def test_admin_menu_ai_quest_wizard_flag() -> None:
    engine = create_async_engine("sqlite+aiosqlite:///:memory:")
    async with engine.begin() as conn:
        await conn.run_sync(FeatureFlag.__table__.create)
    async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

    async with async_session() as db:
        await ensure_known_flags(db)
        await db.commit()
        invalidate_cache()
        req = Request({"type": "http", "headers": []})
        premium_user = SimpleNamespace(role="admin", is_premium=True)
        regular_user = SimpleNamespace(role="admin", is_premium=False)

        def collect_ids(items: list[dict]) -> list[str]:
            ids: list[str] = []
            for it in items:
                ids.append(it["id"])
                ids.extend(collect_ids(it.get("children", [])))
            return ids

        invalidate_menu_cache()
        res = await get_admin_menu(req, premium_user, db)
        data = json.loads(bytes(res.body).decode())
        assert "ai-quests-main" not in collect_ids(data["items"])

        await set_flag(db, FeatureFlagKey.AI_QUEST_WIZARD, True)
        await db.commit()
        invalidate_menu_cache()
        res = await get_admin_menu(req, premium_user, db)
        data = json.loads(bytes(res.body).decode())
        assert "ai-quests-main" in collect_ids(data["items"])

        invalidate_menu_cache()
        res = await get_admin_menu(req, regular_user, db)
        data = json.loads(bytes(res.body).decode())
        assert "ai-quests-main" not in collect_ids(data["items"])

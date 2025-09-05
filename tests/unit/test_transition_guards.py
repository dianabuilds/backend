from __future__ import annotations

import importlib
import sys
from datetime import UTC, datetime, timedelta
from types import SimpleNamespace

import pytest

app_module = importlib.import_module("apps.backend.app")
sys.modules.setdefault("app", app_module)

from app.core.deps import guards  # noqa: E402
from app.core.preview import PreviewContext  # noqa: E402


@pytest.mark.asyncio
async def test_nft_required(monkeypatch):
    transition = SimpleNamespace(id="t1", condition={"nft_required": "rare"})
    user = SimpleNamespace()

    async def _has_nft(u, nft):
        return False

    monkeypatch.setattr(guards, "user_has_nft", _has_nft)
    assert not await guards.check_transition(transition, user)

    async def _has_nft_true(u, nft):
        return True

    monkeypatch.setattr(guards, "user_has_nft", _has_nft_true)
    assert await guards.check_transition(transition, user)


@pytest.mark.asyncio
async def test_tags_subset():
    transition = SimpleNamespace(id="t2", condition={"tags": ["a", "b"]})
    user_ok = SimpleNamespace(tags={"a", "b", "c"})
    user_bad = SimpleNamespace(tags={"a"})
    assert await guards.check_transition(transition, user_ok)
    assert not await guards.check_transition(transition, user_bad)


@pytest.mark.asyncio
async def test_cooldown(monkeypatch):
    now = datetime.now(tz=UTC)
    preview = PreviewContext(now=now)
    transition = SimpleNamespace(id="t3", condition={"cooldown": 60})
    user_wait = SimpleNamespace(transition_cooldowns={"t3": now - timedelta(seconds=30)})
    user_ok = SimpleNamespace(transition_cooldowns={"t3": now - timedelta(seconds=120)})
    assert not await guards.check_transition(transition, user_wait, preview)
    assert await guards.check_transition(transition, user_ok, preview)

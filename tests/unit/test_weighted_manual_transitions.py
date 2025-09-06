from __future__ import annotations

import importlib
import sys
from datetime import datetime
from types import SimpleNamespace
from uuid import uuid4

import pytest

app_module = importlib.import_module("apps.backend.app")
sys.modules.setdefault("app", app_module)
domains_module = importlib.import_module("apps.backend.app.domains")
sys.modules.setdefault("app.domains", domains_module)

from app.domains.navigation.application import transitions_service as ts  # noqa: E402


@pytest.mark.asyncio
async def test_weighted_manual_transitions_sorting(monkeypatch: pytest.MonkeyPatch) -> None:
    t1 = SimpleNamespace(id=uuid4(), weight=1, created_at=datetime(2024, 1, 2))
    t2 = SimpleNamespace(id=uuid4(), weight=2, created_at=datetime(2024, 1, 1))
    t3 = SimpleNamespace(id=uuid4(), weight=2, created_at=datetime(2024, 1, 3))
    transitions = [t1, t2, t3]

    class FakeResult:
        def scalars(self) -> SimpleNamespace:
            return SimpleNamespace(all=lambda: transitions)

    class FakeSession:
        async def execute(self, query) -> FakeResult:  # type: ignore[override]
            return FakeResult()

    async def allow_all(*args, **kwargs):  # noqa: ANN001, D401
        return True

    monkeypatch.setattr(ts, "check_transition", allow_all)

    async def fake_flags(db, header, user):  # noqa: ANN001
        return {"navigation.weighted_manual_transitions"}

    monkeypatch.setattr(ts, "get_effective_flags", fake_flags)

    service = ts.TransitionsService()
    node = SimpleNamespace(id=1)
    user = SimpleNamespace()
    result = await service.get_transitions(FakeSession(), node, user, account_id=1)

    assert [tr.id for tr in result] == [t2.id, t3.id, t1.id]

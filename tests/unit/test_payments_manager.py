from __future__ import annotations

import importlib
import os
import sys

import pytest

os.environ.setdefault("TESTING", "True")
sys.modules.setdefault("app", importlib.import_module("apps.backend.app"))

from app.domains.payments import manager_impl  # noqa: E402


@pytest.mark.asyncio
async def test_verify_payment_without_gateways(monkeypatch) -> None:
    async def fake_verify(token: str, amount: int) -> bool:
        assert token == "tkn"
        assert amount == 1
        return True

    async def fake_load_gateways(db):
        return []

    monkeypatch.setattr(manager_impl, "load_active_gateways", fake_load_gateways)
    monkeypatch.setattr(manager_impl.payment_service, "verify", fake_verify)

    ok, slug = await manager_impl.verify_payment(
        None, amount=1, currency=None, token="tkn"
    )
    assert ok is True
    assert slug is None

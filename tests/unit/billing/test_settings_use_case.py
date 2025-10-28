from __future__ import annotations

from datetime import datetime, timezone
from types import SimpleNamespace
from unittest.mock import AsyncMock

import pytest

from apps.backend.domains.platform.billing.application.use_cases.settings import (
    BillingSettingsUseCase,
)


@pytest.mark.asyncio
async def test_build_bundle_enriches_summary_with_wallet() -> None:
    service = SimpleNamespace(
        get_summary_for_user=AsyncMock(
            return_value={
                "plan": None,
                "subscription": None,
                "payment": {"mode": "evm_wallet", "title": "Wallet"},
                "debt": {"amount_cents": 0, "is_overdue": False},
                "last_payment": None,
            }
        ),
        get_history_for_user=AsyncMock(
            return_value={"items": [], "coming_soon": False}
        ),
    )
    verified_at = datetime(2024, 5, 1, 12, 0, tzinfo=timezone.utc).isoformat()
    wallet = SimpleNamespace(
        address="0x1234",
        chain_id="0x89",
        verified_at=datetime.fromisoformat(verified_at),
    )
    limits = SimpleNamespace(
        can_change_username=True,
        next_username_change_at=None,
        can_change_email=True,
        next_email_change_at=None,
    )
    profile_view = SimpleNamespace(
        id="user-1",
        username="demo",
        email="demo@example.com",
        pending_email=None,
        bio=None,
        avatar_url=None,
        role="user",
        wallet=wallet,
        limits=limits,
    )
    profile_service = SimpleNamespace(get_profile=AsyncMock(return_value=profile_view))

    use_case = BillingSettingsUseCase(service=service, profile_service=profile_service)

    bundle = await use_case.build_bundle("user-1")

    service.get_summary_for_user.assert_awaited_once_with("user-1")
    service.get_history_for_user.assert_awaited_once_with("user-1")
    profile_service.get_profile.assert_awaited_once_with("user-1")

    assert bundle["wallet"]["address"] == "0x1234"
    assert bundle["wallet"]["is_verified"] is True
    assert bundle["wallet"]["status"] == "connected"
    assert bundle["summary"]["wallet"]["address"] == "0x1234"
    assert bundle["summary"]["payment"]["status"] == "wallet_connected"


@pytest.mark.asyncio
async def test_build_bundle_handles_missing_wallet() -> None:
    service = SimpleNamespace(
        get_summary_for_user=AsyncMock(
            return_value={
                "plan": None,
                "subscription": None,
                "payment": {"mode": "evm_wallet", "title": "Wallet"},
                "debt": None,
                "last_payment": None,
            }
        ),
        get_history_for_user=AsyncMock(return_value={"items": [], "coming_soon": True}),
    )
    profile_service = SimpleNamespace(
        get_profile=AsyncMock(side_effect=ValueError("profile_not_found"))
    )

    use_case = BillingSettingsUseCase(service=service, profile_service=profile_service)

    bundle = await use_case.build_bundle("user-2")

    assert bundle["wallet"] is None
    assert bundle["summary"]["wallet"] is None
    assert bundle["summary"]["payment"]["status"] == "wallet_missing"

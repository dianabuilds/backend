from __future__ import annotations

from datetime import UTC, datetime

from domains.product.profile.application.profile_presenter import (
    build_avatar_response,
    build_email_change_response,
    profile_etag,
    profile_to_dict,
)
from domains.product.profile.domain.results import (
    EmailChangeRequest,
    ProfileLimitsView,
    ProfileView,
    WalletView,
)
from packages.core.settings_contract import compute_etag


def _sample_profile_view() -> ProfileView:
    wallet = WalletView(
        address="0x123",
        chain_id="1",
        verified_at=datetime(2024, 1, 2, 3, 4, 5, tzinfo=UTC),
    )
    limits = ProfileLimitsView(
        can_change_username=False,
        next_username_change_at=datetime(2024, 1, 10, tzinfo=UTC),
        can_change_email=True,
        next_email_change_at=None,
    )
    return ProfileView(
        id="user-1",
        username="hex",
        email="user@example.com",
        pending_email=None,
        bio="hello",
        avatar_url="https://cdn/avatar.png",
        role="creator",
        wallet=wallet,
        limits=limits,
    )


def test_profile_to_dict_serializes_iso_fields() -> None:
    view = _sample_profile_view()
    result = profile_to_dict(view)

    assert result["wallet"]["verified_at"] == "2024-01-02T03:04:05+00:00"
    assert result["limits"]["next_username_change_at"] == "2024-01-10T00:00:00+00:00"
    assert result["limits"]["next_email_change_at"] is None


def test_profile_etag_matches_compute_etag() -> None:
    view = _sample_profile_view()
    payload = profile_to_dict(view)
    assert profile_etag(payload) == compute_etag(payload)
    assert profile_etag(view) == compute_etag(payload)


def test_build_email_change_response() -> None:
    response = build_email_change_response(
        EmailChangeRequest(
            status="pending", pending_email="new@example.com", token="abc"
        ),
    )
    assert response == {
        "status": "pending",
        "pending_email": "new@example.com",
        "token": "abc",
    }


def test_build_avatar_response() -> None:
    now = datetime.now(UTC)
    response = build_avatar_response(
        "https://cdn/avatar.png?ts=" + str(int(now.timestamp()))
    )
    assert response["success"] == 1
    assert response["file"]["url"] == response["url"]

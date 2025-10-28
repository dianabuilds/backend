from __future__ import annotations

import pytest

from packages.core.schema_registry import validate_event_payload


def test_profile_updated_event_valid():
    payload = {"id": "u1", "username": "neo", "bio": None}
    # Should not raise when schema is satisfied
    validate_event_payload("profile.updated.v1", payload)


def test_profile_updated_event_invalid_missing_required():
    with pytest.raises(Exception):
        validate_event_payload("profile.updated.v1", {"id": "u1"})


def test_profile_email_change_requested_event_valid():
    payload = {"id": "user-1", "new_email": "new@example.com"}
    validate_event_payload("profile.email.change.requested.v1", payload)


def test_profile_email_change_requested_event_invalid_missing_email():
    with pytest.raises(Exception):
        validate_event_payload("profile.email.change.requested.v1", {"id": "user-1"})


def test_profile_email_updated_event_valid():
    payload = {"id": "user-1", "email": "ok@example.com"}
    validate_event_payload("profile.email.updated.v1", payload)


def test_profile_email_updated_event_invalid_format():
    with pytest.raises(Exception):
        validate_event_payload(
            "profile.email.updated.v1", {"id": "user-1", "email": "not-an-email"}
        )


def test_profile_wallet_updated_event_valid():
    payload = {
        "id": "user-1",
        "wallet_address": "0xabc123",
        "wallet_chain_id": "1",
    }
    validate_event_payload("profile.wallet.updated.v1", payload)


def test_profile_wallet_updated_event_allows_null_chain():
    payload = {"id": "user-1", "wallet_address": "0xabc123", "wallet_chain_id": None}
    validate_event_payload("profile.wallet.updated.v1", payload)


def test_profile_wallet_updated_event_invalid_missing_address():
    with pytest.raises(Exception):
        validate_event_payload(
            "profile.wallet.updated.v1", {"id": "user-1", "wallet_chain_id": "1"}
        )


def test_profile_wallet_cleared_event_valid():
    payload = {"id": "user-1"}
    validate_event_payload("profile.wallet.cleared.v1", payload)


def test_profile_wallet_cleared_event_invalid_extra_field():
    with pytest.raises(Exception):
        validate_event_payload(
            "profile.wallet.cleared.v1",
            {"id": "user-1", "wallet_address": "0xabc"},
        )

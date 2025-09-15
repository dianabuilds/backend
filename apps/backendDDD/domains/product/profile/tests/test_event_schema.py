from __future__ import annotations

import pytest

from apps.backendDDD.packages.core.schema_registry import validate_event_payload


def test_profile_updated_event_valid():
    payload = {"id": "u1", "username": "neo", "bio": None}
    # Should not raise when schema is satisfied
    validate_event_payload("profile.updated.v1", payload)


def test_profile_updated_event_invalid_missing_required():
    with pytest.raises(Exception):
        validate_event_payload("profile.updated.v1", {"id": "u1"})

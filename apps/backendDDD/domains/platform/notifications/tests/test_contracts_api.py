from __future__ import annotations

import pytest
from jsonschema.exceptions import ValidationError

from apps.backendDDD.packages.core.api_contracts import validate_notifications_request


def test_notifications_contract_accepts_object_payload():
    payload = {"channel": "log", "payload": {"msg": "hello"}}
    # Schema requires any object; should not raise
    validate_notifications_request("/v1/notifications/send", "post", payload)


def test_notifications_contract_rejects_non_object():
    with pytest.raises(ValidationError):
        # type: ignore[arg-type]
        validate_notifications_request("/v1/notifications/send", "post", "not-a-dict")

from __future__ import annotations

import importlib
import sys

sys.modules.setdefault("app", importlib.import_module("apps.backend.app"))

from app.security.passwords import hash_password, verify_password  # noqa: E402


def test_hash_and_verify_password() -> None:
    raw = "s3cret"
    hashed = hash_password(raw)
    assert hashed != raw
    assert verify_password(raw, hashed)
    assert not verify_password("other", hashed)

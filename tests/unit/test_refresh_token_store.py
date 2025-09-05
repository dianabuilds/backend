from __future__ import annotations

import importlib
import os
import sys

import jwt

sys.modules.setdefault("app", importlib.import_module("apps.backend.app"))


def _import_security(monkeypatch):
    """Load security module with minimal settings."""

    defaults = {
        "DATABASE__USERNAME": "1",
        "DATABASE__PASSWORD": "1",
        "DATABASE__HOST": "1",
        "DATABASE__NAME": "1",
        "JWT__SECRET": "1",
        "JWT__AUDIENCE": "test-audience",
        "JWT__ISSUER": "test-issuer",
    }
    for key, value in defaults.items():
        if not os.getenv(key):
            monkeypatch.setenv(key, value)

    sys.modules.pop("apps.backend.app.core.config", None)
    sys.modules.pop("apps.backend.app.core.security", None)
    return importlib.import_module("apps.backend.app.core.security")


def test_refresh_token_rotation(monkeypatch):
    security = _import_security(monkeypatch)

    token1 = security.create_refresh_token("user")
    sub = security.verify_refresh_token(token1)
    assert sub == "user"

    token2 = security.create_refresh_token(sub)

    # old token cannot be reused after rotation
    assert security.verify_refresh_token(token1) is None
    # new token is valid
    assert security.verify_refresh_token(token2) == "user"


def test_refresh_token_expiration(monkeypatch):
    security = _import_security(monkeypatch)
    monkeypatch.setattr(security.settings.jwt, "refresh_expires_days", -1)

    token = security.create_refresh_token("user")
    assert security.verify_refresh_token(token) is None


def test_access_token_expiration(monkeypatch):
    security = _import_security(monkeypatch)
    monkeypatch.setattr(security.settings.jwt, "expires_min", -1)

    token = security.create_access_token("user")
    assert security.verify_access_token(token) is None


def test_access_token_audience_and_issuer(monkeypatch):
    security = _import_security(monkeypatch)

    token = security.create_access_token("user")

    decoded = jwt.decode(
        token,
        security.settings.jwt.secret,
        algorithms=[security.settings.jwt.algorithm],
        audience=security.settings.jwt.audience,
        issuer=security.settings.jwt.issuer,
    )
    assert decoded["aud"] == security.settings.jwt.audience
    assert decoded["iss"] == security.settings.jwt.issuer
    assert security.verify_access_token(token) == "user"

    monkeypatch.setattr(security.settings.jwt, "audience", "other-aud")
    assert security.verify_access_token(token) is None

    monkeypatch.setattr(security.settings.jwt, "audience", decoded["aud"])
    monkeypatch.setattr(security.settings.jwt, "issuer", "other-iss")
    assert security.verify_access_token(token) is None

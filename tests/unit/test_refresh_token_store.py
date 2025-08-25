import importlib
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[3]))
sys.modules.setdefault("app", importlib.import_module("apps.backend.app"))


def _import_security(monkeypatch):
    """Load security module with minimal settings."""

    for key in [
        "DATABASE__USERNAME",
        "DATABASE__PASSWORD",
        "DATABASE__HOST",
        "DATABASE__NAME",
        "JWT__SECRET",
    ]:
        monkeypatch.setenv(key, "1")

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

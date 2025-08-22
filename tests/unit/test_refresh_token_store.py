import importlib
import sys
from pathlib import Path

sys.path.append(str(Path(__file__).resolve().parents[2]))


def test_refresh_token_rotation(monkeypatch):
    # provide minimal env so settings can initialize
    for key in [
        "DATABASE__USERNAME",
        "DATABASE__PASSWORD",
        "DATABASE__HOST",
        "DATABASE__NAME",
        "JWT__SECRET",
    ]:
        monkeypatch.setenv(key, "1")

    sys.modules.pop("app.core.config", None)
    sys.modules.pop("app.core.security", None)
    security = importlib.import_module("app.core.security")

    token = security.create_refresh_token("user")
    assert security.verify_refresh_token(token) == "user"
    # token cannot be reused after rotation
    assert security.verify_refresh_token(token) is None

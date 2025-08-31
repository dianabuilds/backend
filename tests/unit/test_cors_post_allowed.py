import importlib
import pathlib
import sys

from starlette.testclient import TestClient


def test_cors_allows_post(monkeypatch):
    # Configure environment without POST to simulate misconfiguration
    monkeypatch.setenv("APP_CORS_ALLOW_METHODS", '["GET","PUT","DELETE","PATCH"]')
    monkeypatch.setenv("TESTING", "1")
    monkeypatch.setenv("AUTH__REDIS_URL", "redis://localhost:6379/0")
    monkeypatch.setenv("DATABASE__HOST", "localhost")
    monkeypatch.setenv("DATABASE__USERNAME", "user")
    monkeypatch.setenv("DATABASE__PASSWORD", "pass")
    monkeypatch.setenv("DATABASE__NAME", "test")
    # Ensure origin is allowed and not affected by other tests
    monkeypatch.delenv("CORS_ALLOW_ORIGINS", raising=False)
    monkeypatch.setenv("APP_CORS_ALLOW_ORIGINS", '["http://example.com"]')

    # Reload settings and app to apply new environment
    sys.path.append(str(pathlib.Path(__file__).resolve().parents[2] / "apps/backend"))

    import app.core.config as config_module
    import app.core.settings as settings_module

    importlib.reload(settings_module)
    importlib.reload(config_module)
    import app.main as main_module

    importlib.reload(main_module)

    client = TestClient(main_module.app)
    headers = {
        "Origin": "http://example.com",
        "Access-Control-Request-Method": "POST",
    }
    resp = client.options("/admin/workspaces", headers=headers)
    assert resp.status_code == 200
    assert "POST" in resp.headers.get("access-control-allow-methods", "")

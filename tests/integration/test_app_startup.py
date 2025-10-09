from __future__ import annotations

import importlib
import sys

from fastapi.testclient import TestClient


def test_app_startup_without_external_services(monkeypatch):
    monkeypatch.setenv("APP_ENV", "test")
    monkeypatch.delenv("APP_DATABASE_URL", raising=False)
    monkeypatch.delenv("APP_REDIS_URL", raising=False)
    monkeypatch.delenv("REDIS_URL", raising=False)

    module_name = "apps.backend.app.api_gateway.main"
    sys.modules.pop(module_name, None)
    main_module = importlib.import_module(module_name)

    with TestClient(main_module.app) as client:
        response = client.get("/healthz")
        assert response.status_code == 200
        data = response.json()
        assert data.get("ok") is True
        assert getattr(client.app.state, "test_mode", False) is True

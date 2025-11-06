from __future__ import annotations

from packages.core.config import load_settings


def test_ai_health_and_generate(app_client):
    h = app_client.get("/v1/ai/health")
    assert h.status_code == 200, h.text
    assert h.json()["status"] in {"ok", "unavailable"}

    settings = load_settings()
    csrf_value = "csrf-smoke"
    app_client.cookies.set(settings.auth_csrf_cookie_name, csrf_value)
    headers = {settings.auth_csrf_header_name: csrf_value}

    g = app_client.post("/v1/ai/generate", json={"prompt": "hello"}, headers=headers)
    assert g.status_code == 200, g.text
    body = g.json()
    assert isinstance(body.get("result"), str)

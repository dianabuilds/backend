from __future__ import annotations


def test_ai_health_and_generate(app_client):
    h = app_client.get("/v1/ai/health")
    assert h.status_code == 200, h.text
    assert h.json()["status"] in {"ok", "unavailable"}

    g = app_client.post("/v1/ai/generate", json={"prompt": "hello"})
    assert g.status_code == 200, g.text
    body = g.json()
    assert isinstance(body.get("result"), str)

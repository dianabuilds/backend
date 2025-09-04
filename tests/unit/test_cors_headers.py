from starlette.testclient import TestClient

from app.main import app


def test_cors_allows_custom_headers():
    client = TestClient(app)
    resp = client.options(
        "/admin/media",
        headers={
            "Origin": "http://client.example",
            "Access-Control-Request-Method": "POST",
            "Access-Control-Request-Headers": (
                "x-feature-flags, x-preview-token, "
                "x-workspace-id, x-blocksketch-workspace-id"
            ),
        },
    )
    assert resp.status_code == 200
    allowed = resp.headers.get("access-control-allow-headers", "").lower()
    assert "x-feature-flags" in allowed
    assert "x-preview-token" in allowed
    assert "x-workspace-id" in allowed
    assert "x-blocksketch-workspace-id" in allowed

from __future__ import annotations

from uuid import uuid4

from tests.conftest import add_auth, make_jwt


def test_premium_me_limits_free_plan(app_client):
    uid = str(uuid4())
    tok = make_jwt(uid)
    add_auth(app_client, tok)
    r = app_client.get("/v1/premium/me/limits")
    assert r.status_code == 200, r.text
    body = r.json()
    assert body["plan"] == "free"
    assert (
        "limits" in body
        and "stories" in body["limits"]["month"]
        or "month" in body["limits"]["stories"]
    )

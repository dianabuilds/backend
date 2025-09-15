from __future__ import annotations

from tests.conftest import add_auth, make_jwt
from uuid import uuid4


def test_navigation_next_no_candidates(app_client):
    uid = str(uuid4())
    tok = make_jwt(uid)
    add_auth(app_client, tok)
    r = app_client.post("/v1/navigation/next", json={"strategy": "random"})
    assert r.status_code == 200, r.text
    body = r.json()
    assert body["node_id"] is None
    assert body["reason"] in {"random", "no_candidates"}


from __future__ import annotations

from .conftest import add_auth, make_jwt
from uuid import uuid4


def test_moderation_list_create_add_note(app_client):
    # Admin key required; also CSRF cookie/header handled by conftest add_auth
    uid = str(uuid4())
    tok = make_jwt(uid, role="admin")
    add_auth(app_client, tok)
    headers = {"X-Admin-Key": "adminkey"}

    # Initially list empty
    r0 = app_client.get("/v1/moderation/cases", headers=headers)
    assert r0.status_code == 200, r0.text

    # Create case
    c = app_client.post("/v1/moderation/cases", json={"title": "t", "description": "d"}, headers=headers)
    assert c.status_code == 200, c.text
    cid = c.json()["id"]

    # Add note
    n = app_client.post(f"/v1/moderation/cases/{cid}/notes", json={"text": "ping"}, headers=headers)
    assert n.status_code == 200, n.text
    assert n.json()["text"] == "ping"


from __future__ import annotations
from uuid import uuid4

import pytest

from packages.core.config import load_settings

from tests.conftest import add_auth, make_jwt

ADMIN_KEY = str(load_settings().admin_api_key or "")
if not ADMIN_KEY:
    pytest.skip(
        "APP_ADMIN_API_KEY is required for admin endpoints", allow_module_level=True
    )


def test_worlds_crud_and_characters(app_client):
    uid = str(uuid4())
    tok = make_jwt(uid, role="admin")
    add_auth(app_client, tok)
    headers = {"X-Admin-Key": ADMIN_KEY}

    # List initial state
    r0 = app_client.get("/v1/admin/worlds", headers=headers)
    assert r0.status_code == 200, r0.text
    baseline = r0.json()

    # Create world
    c = app_client.post(
        "/v1/admin/worlds",
        json={"title": "World", "locale": "en", "description": "d"},
        headers=headers,
    )
    assert c.status_code == 200, c.text
    wid = c.json()["id"]

    # Update world
    u = app_client.patch(
        f"/v1/admin/worlds/{wid}",
        json={"title": "World2"},
        headers=headers,
    )
    assert u.status_code == 200, u.text
    assert u.json()["title"] == "World2"

    # List characters empty for new world
    lc = app_client.get(f"/v1/admin/worlds/{wid}/characters", headers=headers)
    assert lc.status_code == 200, lc.text
    assert lc.json() == []

    # Create character
    cc = app_client.post(
        f"/v1/admin/worlds/{wid}/characters",
        json={"name": "NPC", "role": "guide"},
        headers=headers,
    )
    assert cc.status_code == 200, cc.text
    cid = cc.json()["id"]

    # Update character
    uc = app_client.patch(
        f"/v1/admin/worlds/characters/{cid}",
        json={"description": "updated"},
        headers=headers,
    )
    assert uc.status_code == 200, uc.text
    assert uc.json()["description"] == "updated"

    # Delete character
    dc = app_client.delete(f"/v1/admin/worlds/characters/{cid}", headers=headers)
    assert dc.status_code == 200, dc.text

    # Delete world
    dw = app_client.delete(f"/v1/admin/worlds/{wid}", headers=headers)
    assert dw.status_code == 200, dw.text

    r_final = app_client.get("/v1/admin/worlds", headers=headers)
    assert r_final.status_code == 200, r_final.text
    ids = {item["id"] for item in r_final.json()}
    assert wid not in ids
    assert len(r_final.json()) == len(baseline)

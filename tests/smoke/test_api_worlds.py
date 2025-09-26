from __future__ import annotations

from uuid import uuid4

from tests.conftest import add_auth, make_jwt


def test_worlds_crud_and_characters(app_client):
    tenant = str(uuid4())
    uid = str(uuid4())
    tok = make_jwt(uid, role="admin")
    add_auth(app_client, tok)
    headers = {"X-Admin-Key": "adminkey"}

    # List empty
    r0 = app_client.get(f"/v1/admin/worlds?tenant_id={tenant}", headers=headers)
    assert r0.status_code == 200, r0.text
    assert r0.json() == []

    # Create world
    c = app_client.post(
        f"/v1/admin/worlds?tenant_id={tenant}",
        json={"title": "World", "locale": "en", "description": "d"},
        headers=headers,
    )
    assert c.status_code == 200, c.text
    wid = c.json()["id"]

    # Update world
    u = app_client.patch(
        f"/v1/admin/worlds/{wid}?tenant_id={tenant}",
        json={"title": "World2"},
        headers=headers,
    )
    assert u.status_code == 200, u.text
    assert u.json()["title"] == "World2"

    # List characters empty
    lc = app_client.get(f"/v1/admin/worlds/{wid}/characters?tenant_id={tenant}", headers=headers)
    assert lc.status_code == 200, lc.text
    assert lc.json() == []

    # Create character
    cc = app_client.post(
        f"/v1/admin/worlds/{wid}/characters?tenant_id={tenant}",
        json={"name": "NPC", "role": "guide"},
        headers=headers,
    )
    assert cc.status_code == 200, cc.text
    cid = cc.json()["id"]

    # Update character
    uc = app_client.patch(
        f"/v1/admin/worlds/characters/{cid}?tenant_id={tenant}",
        json={"description": "updated"},
        headers=headers,
    )
    assert uc.status_code == 200, uc.text
    assert uc.json()["description"] == "updated"

    # Delete character
    dc = app_client.delete(f"/v1/admin/worlds/characters/{cid}?tenant_id={tenant}", headers=headers)
    assert dc.status_code == 200, dc.text

    # Delete world
    dw = app_client.delete(f"/v1/admin/worlds/{wid}?tenant_id={tenant}", headers=headers)
    assert dw.status_code == 200, dw.text

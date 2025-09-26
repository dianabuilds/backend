from __future__ import annotations


def test_tags_admin_list_and_blacklist(app_client):
    headers = {"X-Admin-Key": "adminkey"}
    # list (empty)
    r = app_client.get("/v1/admin/tags/list", headers=headers)
    assert r.status_code == 200, r.text
    # blacklist add/get/delete
    add = app_client.post(
        "/v1/admin/tags/blacklist", json={"slug": "spam", "reason": "test"}, headers=headers
    )
    assert add.status_code == 200, add.text
    bl = app_client.get("/v1/admin/tags/blacklist", headers=headers)
    assert bl.status_code == 200 and any(x["slug"] == "spam" for x in bl.json())
    rm = app_client.delete("/v1/admin/tags/blacklist/spam", headers=headers)
    assert rm.status_code == 200, rm.text

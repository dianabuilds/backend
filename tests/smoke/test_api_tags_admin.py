from __future__ import annotations

import pytest

from packages.core.config import load_settings

_ADMIN_SECRET = load_settings().admin_api_key
ADMIN_KEY = _ADMIN_SECRET.get_secret_value() if _ADMIN_SECRET else ""
if not ADMIN_KEY:
    pytest.skip(
        "APP_ADMIN_API_KEY is required for admin endpoints", allow_module_level=True
    )


def test_tags_admin_list_and_blacklist(app_client):
    headers = {"X-Admin-Key": ADMIN_KEY}
    # list (empty)
    r = app_client.get("/v1/admin/tags/list", headers=headers)
    assert r.status_code == 200, r.text
    # blacklist add/get/delete
    add = app_client.post(
        "/v1/admin/tags/blacklist",
        json={"slug": "spam", "reason": "test"},
        headers=headers,
    )
    assert add.status_code == 200, add.text
    bl = app_client.get("/v1/admin/tags/blacklist", headers=headers)
    assert bl.status_code == 200 and any(x["slug"] == "spam" for x in bl.json())
    rm = app_client.delete("/v1/admin/tags/blacklist/spam", headers=headers)
    assert rm.status_code == 200, rm.text

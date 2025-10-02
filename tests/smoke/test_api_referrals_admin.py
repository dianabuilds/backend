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


def test_referrals_admin_codes_and_events(app_client):
    headers = {"X-Admin-Key": ADMIN_KEY}
    # list codes empty
    r = app_client.get("/v1/admin/referrals/codes", headers=headers)
    assert r.status_code == 200, r.text

    # activate/deactivate personal code for a user
    uid = uuid4()
    # Need auth for CSRF cookie set (conftest handles)
    tok = make_jwt(str(uid))
    add_auth(app_client, tok)
    act = app_client.post(
        f"/v1/admin/referrals/codes/{uid}/activate",
        json={"reason": "init"},
        headers=headers,
    )
    assert act.status_code == 200, act.text
    de = app_client.post(
        f"/v1/admin/referrals/codes/{uid}/deactivate",
        json={"reason": "off"},
        headers=headers,
    )
    assert de.status_code == 200, de.text

    # events export (should succeed even if empty)
    exp = app_client.get("/v1/admin/referrals/events/export", headers=headers)
    assert exp.status_code == 200
    assert exp.headers.get("content-type", "").startswith("text/csv")

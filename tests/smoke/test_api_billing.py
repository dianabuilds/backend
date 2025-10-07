from __future__ import annotations

from types import SimpleNamespace
from uuid import uuid4
from unittest.mock import AsyncMock

from packages.core.config import load_settings
from tests.conftest import add_auth, make_jwt


class _Plan(SimpleNamespace):
    pass


def _csrf_headers() -> dict[str, str]:
    settings = load_settings()
    return {settings.auth_csrf_header_name: "csrf-test"}


def test_public_billing_plans(app_client):
    container = app_client.app.state.container
    original = container.billing.service.list_plans
    plans = [_Plan(id="p1", slug="basic", title="Basic")]
    container.billing.service.list_plans = AsyncMock(return_value=plans)
    try:
        response = app_client.get("/v1/billing/plans")
    finally:
        container.billing.service.list_plans = original
    assert response.status_code == 200, response.text
    assert response.json() == {"items": [plans[0].__dict__]}


def test_admin_billing_list_plans(app_client):
    uid = str(uuid4())
    token = make_jwt(uid, role="admin")
    add_auth(app_client, token)

    container = app_client.app.state.container
    original_list_all = container.billing.plans.list_all
    plans = [_Plan(id="p2", slug="enterprise", title="Enterprise")]
    container.billing.plans.list_all = AsyncMock(return_value=plans)
    try:
        response = app_client.get("/v1/billing/admin/plans/all")
    finally:
        container.billing.plans.list_all = original_list_all
    assert response.status_code == 200, response.text
    assert response.json() == {"items": [plans[0].__dict__]}

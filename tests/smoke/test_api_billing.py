from __future__ import annotations

import os
from types import SimpleNamespace
from uuid import uuid4
from unittest.mock import AsyncMock

from packages.core.config import load_settings
from tests.conftest import add_auth, make_jwt

os.environ.setdefault("APP_DATABASE_URL", "")
os.environ.setdefault("DATABASE_URL", "")


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

    state = app_client.app.state
    state.__dict__.pop("_billing_use_cases", None)

    from apps.backend.domains.platform.iam import security

    original_get_current_user = security.get_current_user
    security.get_current_user = AsyncMock(return_value={"sub": uid, "role": "admin"})

    container = state.container
    original_list_all = container.billing.plans.list_all
    plans = [_Plan(id="p2", slug="enterprise", title="Enterprise")]
    container.billing.plans.list_all = AsyncMock(return_value=plans)
    try:
        response = app_client.get("/v1/billing/admin/plans/all")
    finally:
        container.billing.plans.list_all = original_list_all
        security.get_current_user = original_get_current_user
        state.__dict__.pop("_billing_use_cases", None)
    assert response.status_code == 200, response.text
    assert response.json() == {"items": [plans[0].__dict__]}


def test_overview_dashboard_requires_finance_ops(app_client):
    token = make_jwt(str(uuid4()), role="finance_ops")
    add_auth(app_client, token)

    state = app_client.app.state
    state.__dict__.pop("_billing_use_cases", None)

    from apps.backend.domains.platform.iam import security

    original_get_current_user = security.get_current_user
    security.get_current_user = AsyncMock(
        return_value={"sub": "finance", "role": "finance_ops"}
    )

    container = state.container
    original_metrics = container.billing.analytics
    container.billing.analytics = SimpleNamespace(
        kpi=AsyncMock(return_value={"success": 1}),
        subscription_metrics=AsyncMock(return_value={"active_subs": 1}),
        revenue_timeseries=AsyncMock(
            return_value=[{"day": "2024-01-01", "amount": 1.0}]
        ),
        network_breakdown=AsyncMock(return_value=[{"network": "polygon"}]),
    )
    original_ledger = container.billing.service.ledger
    container.billing.service.ledger = SimpleNamespace(
        list_recent=AsyncMock(return_value=[])
    )
    try:
        response = app_client.get("/v1/billing/overview/dashboard")
    finally:
        container.billing.analytics = original_metrics
        container.billing.service.ledger = original_ledger
        security.get_current_user = original_get_current_user
        state.__dict__.pop("_billing_use_cases", None)
    assert response.status_code == 200
    body = response.json()
    assert "kpi" in body

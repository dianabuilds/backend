from __future__ import annotations

from dataclasses import dataclass
from types import SimpleNamespace
from typing import Any
from unittest.mock import AsyncMock

import pytest

from apps.backend.domains.platform.billing.application.use_cases.exceptions import (
    BillingUseCaseError,
)
from apps.backend.domains.platform.billing.application.use_cases import plans_admin
from apps.backend.domains.platform.billing.application.use_cases.plans_admin import (
    PlansAdminUseCase,
)


@dataclass
class DummyPlan:
    id: str
    slug: str
    title: str
    price_cents: int = 0
    currency: str | None = None
    is_active: bool = True
    order: int = 100
    monthly_limits: dict | None = None
    features: dict | None = None


@pytest.mark.asyncio
async def test_upsert_fetches_existing_plan_and_logs_audit(monkeypatch) -> None:
    existing = DummyPlan(id="1", slug="basic", title="Basic")
    created = DummyPlan(id="2", slug="basic", title="Basic")
    repo = SimpleNamespace(
        get_by_slug=AsyncMock(return_value=existing),
        upsert=AsyncMock(return_value=created),
        list_all=AsyncMock(),
        delete=AsyncMock(),
    )
    audit_service = SimpleNamespace(name="audit")
    audit_repo = SimpleNamespace(list=AsyncMock(return_value=[]))
    captured: list[tuple] = []

    async def fake_safe(service, payload, **kwargs):
        captured.append((service, payload, kwargs))

    monkeypatch.setattr(plans_admin, "safe_audit_log", fake_safe)

    use_case = PlansAdminUseCase(
        plans=repo, audit_service=audit_service, audit_repo=audit_repo
    )

    result = await use_case.upsert(payload={"slug": "basic"}, actor_id="admin")

    assert result == {"plan": created.__dict__}
    repo.get_by_slug.assert_awaited_once_with("basic")
    repo.upsert.assert_awaited_once()
    assert captured, "expected audit helper to be invoked"
    service, payload, kwargs = captured[0]
    assert service is audit_service
    assert payload.action == "plan.upsert"
    assert payload.resource_id == "basic"
    assert payload.before == existing.__dict__
    assert kwargs["error_slug"] == "billing_plan_audit_failed"


@pytest.mark.asyncio
async def test_upsert_without_slug_skips_lookup(monkeypatch) -> None:
    repo = SimpleNamespace(
        get_by_slug=AsyncMock(),
        upsert=AsyncMock(return_value=DummyPlan(id="2", slug="auto", title="Auto")),
        list_all=AsyncMock(),
        delete=AsyncMock(),
    )
    audit_repo = SimpleNamespace(list=AsyncMock(return_value=[]))

    async def fake_safe(*_args, **_kwargs):
        return None

    monkeypatch.setattr(plans_admin, "safe_audit_log", fake_safe)

    use_case = PlansAdminUseCase(
        plans=repo,
        audit_service=SimpleNamespace(),
        audit_repo=audit_repo,
    )

    await use_case.upsert(payload={}, actor_id=None)

    repo.get_by_slug.assert_not_called()
    repo.upsert.assert_awaited_once()


@pytest.mark.asyncio
async def test_delete_requires_plan_id() -> None:
    use_case = PlansAdminUseCase(
        plans=SimpleNamespace(),
        audit_service=SimpleNamespace(),
        audit_repo=SimpleNamespace(list=AsyncMock(return_value=[])),
    )

    with pytest.raises(BillingUseCaseError):
        await use_case.delete(plan_id="")


@pytest.mark.asyncio
async def test_list_all_serializes_plans() -> None:
    plans = [DummyPlan(id="p1", slug="basic", title="Basic")]
    repo = SimpleNamespace(
        list_all=AsyncMock(return_value=plans),
    )
    use_case = PlansAdminUseCase(
        plans=repo,
        audit_service=SimpleNamespace(),
        audit_repo=SimpleNamespace(list=AsyncMock(return_value=[])),
    )

    result = await use_case.list_all()

    assert result == {"items": [plans[0].__dict__]}
    repo.list_all.assert_awaited_once()


@pytest.mark.asyncio
async def test_bulk_limits_merges_existing_limits() -> None:
    existing = DummyPlan(
        id="1",
        slug="pro",
        title="Pro",
        monthly_limits={"seats": 5},
    )
    updated = DummyPlan(id="1", slug="pro", title="Pro", monthly_limits={"seats": 10})
    secondary = DummyPlan(id="2", slug="new", title="New")
    repo = SimpleNamespace(
        get_by_slug=AsyncMock(side_effect=[existing, None]),
        upsert=AsyncMock(side_effect=[updated, secondary]),
    )
    use_case = PlansAdminUseCase(
        plans=repo,
        audit_service=SimpleNamespace(),
        audit_repo=SimpleNamespace(list=AsyncMock(return_value=[])),
    )

    items: list[dict[str, Any]] = [
        {"slug": "pro", "monthly_limits": {"seats": 10}},
        {"slug": " "},
        {"slug": "new", "monthly_limits": {"seats": 1}},
    ]
    result = await use_case.bulk_limits(items=items)

    assert result == {"items": [updated.__dict__, secondary.__dict__]}
    assert repo.get_by_slug.await_count == 2
    assert repo.upsert.await_count == 2


@pytest.mark.asyncio
async def test_audit_filters_records() -> None:
    records = [
        {"resource_type": "plan", "resource_id": "basic", "id": 1},
        {"resource_type": "plan", "resource_id": "other", "id": 2},
        {"resource_type": "user", "resource_id": "basic", "id": 3},
    ]
    audit_repo = SimpleNamespace(list=AsyncMock(return_value=records))
    use_case = PlansAdminUseCase(
        plans=SimpleNamespace(),
        audit_service=SimpleNamespace(),
        audit_repo=audit_repo,
    )

    result = await use_case.audit(slug="basic", limit=5)

    assert result == {"items": [records[0]]}
    audit_repo.list.assert_awaited_once_with(limit=5)

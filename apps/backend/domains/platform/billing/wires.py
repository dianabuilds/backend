from __future__ import annotations

from dataclasses import dataclass

from domains.platform.billing.adapters.provider_mock import MockProvider
from domains.platform.billing.adapters.repos_sql import (
    SQLLedgerRepo,
    SQLPlanRepo,
    SQLSubscriptionRepo,
)
from domains.platform.billing.application.service import BillingService
from packages.core.config import Settings, load_settings, to_async_dsn


@dataclass
class BillingContainer:
    settings: Settings
    service: BillingService
    plans: SQLPlanRepo


def build_container(settings: Settings | None = None) -> BillingContainer:
    s = settings or load_settings()
    dsn = to_async_dsn(s.database_url)
    plans = SQLPlanRepo(dsn)
    subs = SQLSubscriptionRepo(dsn)
    ledger = SQLLedgerRepo(dsn)
    provider = MockProvider()
    svc = BillingService(plans=plans, subs=subs, ledger=ledger, provider=provider)
    return BillingContainer(settings=s, service=svc, plans=plans)


__all__ = ["BillingContainer", "build_container"]

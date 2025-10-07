from __future__ import annotations

from dataclasses import dataclass

from sqlalchemy.ext.asyncio import AsyncEngine

from domains.platform.billing.adapters.provider_mock import MockProvider
from domains.platform.billing.adapters.sql.contracts import SQLContractsRepo
from domains.platform.billing.adapters.sql.crypto_config import SQLCryptoConfigRepo
from domains.platform.billing.adapters.sql.repositories import (
    SQLGatewaysRepo,
    SQLLedgerRepo,
    SQLPlanRepo,
    SQLSubscriptionRepo,
)
from domains.platform.billing.application.service import BillingService
from domains.platform.billing.infrastructure import (
    SQLBillingAnalyticsRepo,
    SQLBillingHistoryRepo,
    SQLBillingSummaryRepo,
)
from packages.core.config import Settings, load_settings, to_async_dsn
from packages.core.db import get_async_engine


@dataclass
class BillingContainer:
    settings: Settings
    service: BillingService
    plans: SQLPlanRepo
    gateways: SQLGatewaysRepo
    contracts: SQLContractsRepo
    crypto_config_store: SQLCryptoConfigRepo
    analytics: SQLBillingAnalyticsRepo
    summary: SQLBillingSummaryRepo
    history: SQLBillingHistoryRepo


def build_container(settings: Settings | None = None) -> BillingContainer:
    s = settings or load_settings()
    dsn = to_async_dsn(s.database_url)
    engine: AsyncEngine = get_async_engine("billing", url=dsn)
    plans = SQLPlanRepo(engine)
    subs = SQLSubscriptionRepo(engine)
    ledger = SQLLedgerRepo(engine)
    gateways = SQLGatewaysRepo(engine)
    provider = MockProvider()
    analytics = SQLBillingAnalyticsRepo(engine)
    summary = SQLBillingSummaryRepo(engine)
    history = SQLBillingHistoryRepo(engine)
    svc = BillingService(
        plans=plans,
        subs=subs,
        ledger=ledger,
        provider=provider,
        summary_repo=summary,
        history_repo=history,
    )
    contracts = SQLContractsRepo(engine)
    crypto_cfg = SQLCryptoConfigRepo(engine)
    return BillingContainer(
        settings=s,
        service=svc,
        plans=plans,
        gateways=gateways,
        contracts=contracts,
        crypto_config_store=crypto_cfg,
        analytics=analytics,
        summary=summary,
        history=history,
    )


__all__ = ["BillingContainer", "build_container"]

from __future__ import annotations

from dataclasses import dataclass

from domains.platform.billing.adapters.contracts_sql import SQLContractsRepo
from domains.platform.billing.adapters.crypto_config_sql import SQLCryptoConfigRepo
from domains.platform.billing.adapters.provider_mock import MockProvider
from domains.platform.billing.adapters.repos_sql import (
    SQLGatewaysRepo,
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
    gateways: SQLGatewaysRepo
    contracts: SQLContractsRepo
    crypto_config_store: SQLCryptoConfigRepo


def build_container(settings: Settings | None = None) -> BillingContainer:
    s = settings or load_settings()
    dsn = to_async_dsn(s.database_url)
    plans = SQLPlanRepo(dsn)
    subs = SQLSubscriptionRepo(dsn)
    ledger = SQLLedgerRepo(dsn)
    gateways = SQLGatewaysRepo(dsn)
    provider = MockProvider()
    svc = BillingService(plans=plans, subs=subs, ledger=ledger, provider=provider)
    contracts = SQLContractsRepo(dsn)
    crypto_cfg = SQLCryptoConfigRepo(dsn)
    return BillingContainer(
        settings=s,
        service=svc,
        plans=plans,
        gateways=gateways,
        contracts=contracts,
        crypto_config_store=crypto_cfg,
    )


__all__ = ["BillingContainer", "build_container"]

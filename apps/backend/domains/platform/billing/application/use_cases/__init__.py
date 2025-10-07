from __future__ import annotations

from dataclasses import dataclass

from domains.platform.audit.application.service import AuditService
from domains.platform.audit.ports.repo import AuditLogRepository
from domains.platform.billing.application.service import BillingService
from domains.platform.billing.ports import (
    BillingAnalyticsRepo,
    ContractsRepo,
    CryptoConfigRepo,
    GatewayRepo,
    PlanRepo,
)

from .contracts_admin import ContractsAdminUseCase
from .metrics import MetricsAdminUseCase
from .plans_admin import PlansAdminUseCase
from .providers_admin import ProvidersAdminUseCase
from .public import PublicBillingUseCases
from .settings import BillingSettingsUseCase, ProfileServiceProtocol


@dataclass
class AdminUseCases:
    plans: PlansAdminUseCase
    providers: ProvidersAdminUseCase
    contracts: ContractsAdminUseCase
    metrics: MetricsAdminUseCase


@dataclass
class BillingUseCases:
    public: PublicBillingUseCases
    admin: AdminUseCases
    settings: BillingSettingsUseCase


def build_use_cases(
    *,
    service: BillingService,
    plans: PlanRepo,
    gateways: GatewayRepo,
    contracts: ContractsRepo,
    crypto_store: CryptoConfigRepo,
    analytics: BillingAnalyticsRepo,
    profile_service: ProfileServiceProtocol,
    audit_service: AuditService,
    audit_repo: AuditLogRepository,
    webhook_secret: str | None,
) -> BillingUseCases:
    if audit_service is None or audit_repo is None:
        raise RuntimeError("audit container is unavailable for billing")
    public = PublicBillingUseCases(
        service=service, contracts=contracts, webhook_secret=webhook_secret
    )
    admin = AdminUseCases(
        plans=PlansAdminUseCase(
            plans=plans, audit_service=audit_service, audit_repo=audit_repo
        ),
        providers=ProvidersAdminUseCase(gateways=gateways, ledger=service.ledger),
        contracts=ContractsAdminUseCase(contracts=contracts),
        metrics=MetricsAdminUseCase(
            service=service, analytics=analytics, crypto_store=crypto_store
        ),
    )
    settings = BillingSettingsUseCase(service=service, profile_service=profile_service)
    return BillingUseCases(public=public, admin=admin, settings=settings)


__all__ = [
    "BillingUseCases",
    "AdminUseCases",
    "BillingSettingsUseCase",
    "ProfileServiceProtocol",
    "build_use_cases",
]

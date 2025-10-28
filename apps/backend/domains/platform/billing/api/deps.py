from __future__ import annotations

from fastapi import Request
from pydantic import SecretStr

from apps.backend.app.api_gateway.routers import get_container
from packages.fastapi_rate_limit import optional_rate_limiter

from ..application.use_cases import (
    BillingSettingsUseCase,
    BillingUseCases,
    build_use_cases,
)
from ..application.use_cases.contracts_admin import ContractsAdminUseCase
from ..application.use_cases.metrics import MetricsAdminUseCase
from ..application.use_cases.overview import OverviewUseCases
from ..application.use_cases.plans_admin import PlansAdminUseCase
from ..application.use_cases.providers_admin import ProvidersAdminUseCase
from ..application.use_cases.public import PublicBillingUseCases

CHECKOUT_RATE_LIMITER = optional_rate_limiter(times=5, seconds=60)
_USE_CASES_STATE_KEY = "_billing_use_cases"


def _resolve_use_cases(req: Request) -> BillingUseCases:
    state = req.state
    cached = getattr(state, _USE_CASES_STATE_KEY, None)
    if cached is not None:
        return cached
    container = get_container(req)
    billing = container.billing
    audit = container.audit
    settings = getattr(container, "settings", None)
    webhook_secret: str | None = None
    if settings is not None:
        secret_candidate = getattr(settings, "billing_webhook_secret", None)
        if isinstance(secret_candidate, SecretStr):
            webhook_secret = secret_candidate.get_secret_value()
        elif isinstance(secret_candidate, str):
            webhook_secret = secret_candidate
    use_cases = build_use_cases(
        service=billing.service,
        plans=billing.plans,
        gateways=billing.gateways,
        contracts=billing.contracts,
        crypto_store=billing.crypto_config_store,
        analytics=billing.analytics,
        profile_service=container.profile_service,
        audit_service=audit.service,
        audit_repo=audit.repo,
        webhook_secret=webhook_secret,
    )
    setattr(state, _USE_CASES_STATE_KEY, use_cases)
    return use_cases


def get_public_use_cases(req: Request) -> PublicBillingUseCases:
    return _resolve_use_cases(req).public


def get_settings_use_case(req: Request) -> BillingSettingsUseCase:
    return _resolve_use_cases(req).settings


def get_admin_plans_use_case(req: Request) -> PlansAdminUseCase:
    return _resolve_use_cases(req).admin.plans


def get_admin_providers_use_case(req: Request) -> ProvidersAdminUseCase:
    return _resolve_use_cases(req).admin.providers


def get_admin_contracts_use_case(req: Request) -> ContractsAdminUseCase:
    return _resolve_use_cases(req).admin.contracts


def get_admin_metrics_use_case(req: Request) -> MetricsAdminUseCase:
    return _resolve_use_cases(req).admin.metrics


def get_overview_use_case(req: Request) -> OverviewUseCases:
    return _resolve_use_cases(req).overview


def get_overview_metrics_use_case(req: Request) -> MetricsAdminUseCase:
    return _resolve_use_cases(req).overview.metrics


def get_actor_id(req: Request) -> str | None:
    ctx = getattr(req.state, "auth_context", None)
    return ctx.get("actor_id") if isinstance(ctx, dict) else None

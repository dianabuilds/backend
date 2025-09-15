from __future__ import annotations

from fastapi import FastAPI

from apps.backendDDD.domains.product.ai.application.service import AIService
from app.bridges.ai_provider_adapter import AIDomainProviderAdapter
from app.bridges.outbox_adapter import SAOutboxAdapter

try:  # pragma: no cover - env dependent
    from config.feature_flags import feature_flags  # type: ignore
except ModuleNotFoundError:  # pragma: no cover
    from apps.backend.config.feature_flags import feature_flags  # type: ignore


def wire_ai_service(app: FastAPI) -> None:
    if not getattr(feature_flags, "ai_v1_enabled", True):
        return
    container = getattr(app.state, "container", None)
    if container is None:
        return
    # Resolve monolith provider from DI container
    try:
        from app.providers.ai import IAIProvider

        provider = container.resolve(IAIProvider)
    except Exception:
        provider = None
    if not provider:
        return
    outbox = SAOutboxAdapter()
    svc = AIService(AIDomainProviderAdapter(provider), outbox=outbox)
    setattr(container, "ai_service", svc)


def include_ai_router(app: FastAPI) -> None:
    if not getattr(feature_flags, "ai_v1_enabled", True):
        return
    from apps.backendDDD.domains.product.ai.api.http import make_router

    app.include_router(make_router())

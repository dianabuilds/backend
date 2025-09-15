from __future__ import annotations

from fastapi import FastAPI

from apps.backendDDD.domains.product.moderation.api.http import make_router

try:  # pragma: no cover
    from config.feature_flags import feature_flags  # type: ignore
except ModuleNotFoundError:  # pragma: no cover
    from apps.backend.config.feature_flags import feature_flags  # type: ignore


def wire_moderation_service(app: FastAPI) -> None:
    if not getattr(feature_flags, "moderation_v1_enabled", True):
        return
    # No global wiring needed: service is composed in API handlers using adapters.
    return


def include_moderation_router(app: FastAPI) -> None:
    if not getattr(feature_flags, "moderation_v1_enabled", True):
        return
    app.include_router(make_router())


from __future__ import annotations

from fastapi import FastAPI

from apps.backendDDD.domains.product.tags.application.service import TagService
from app.bridges.tags_repo_adapter import SATagsRepo
try:  # pragma: no cover - environment-dependent import path
    from config.feature_flags import feature_flags  # type: ignore
except ModuleNotFoundError:  # pragma: no cover
    from apps.backend.config.feature_flags import feature_flags  # type: ignore


def wire_tags_service(app: FastAPI) -> None:
    if not getattr(feature_flags, "tags_v1_enabled", True):
        return
    repo = SATagsRepo()
    svc = TagService(repo)
    container = getattr(app.state, "container", None)
    if container is None:
        app.state.container = type("Container", (), {})()
        container = app.state.container
    setattr(container, "tags_service", svc)


def include_tags_router(app: FastAPI) -> None:
    if not getattr(feature_flags, "tags_v1_enabled", True):
        return
    # Lazy import
    from apps.backendDDD.domains.product.tags.api.http import make_router
    from apps.backendDDD.domains.product.tags.api.admin_http import make_router as admin_router

    app.include_router(make_router())
    app.include_router(admin_router())

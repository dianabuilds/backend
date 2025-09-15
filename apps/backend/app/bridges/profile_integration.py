from __future__ import annotations

import os

from fastapi import FastAPI

from apps.backendDDD.domains.product.profile.application.services import (
    Service as ProfileService,
)
from apps.backendDDD.domains.product.profile.adapters.iam_client import (
    IamClient as ProfileIamClient,
)
from apps.backendDDD.packages.core.flags import Flags

from app.core.config import settings
# Feature flags import with fallback to absolute package path
try:  # pragma: no cover - environment-dependent import path
    from config.feature_flags import feature_flags  # type: ignore
except ModuleNotFoundError:  # pragma: no cover
    from apps.backend.config.feature_flags import feature_flags  # type: ignore
from app.bridges.profile_repo_adapter import SAUserProfileRepo
from app.bridges.outbox_adapter import SAOutboxAdapter


def _sync_security_env() -> None:
    """Align DDD security settings with monolith settings via env vars."""
    os.environ.setdefault("APP_AUTH_JWT_SECRET", settings.jwt.secret)
    os.environ.setdefault("APP_AUTH_JWT_ALGORITHM", settings.jwt.algorithm)
    os.environ.setdefault("APP_AUTH_CSRF_COOKIE_NAME", settings.csrf.cookie_name)
    os.environ.setdefault("APP_AUTH_CSRF_HEADER_NAME", settings.csrf.header_name)


def wire_profile_service(app: FastAPI) -> None:
    """Attach DDD Profile service instance to app.state.container."""
    if not feature_flags.profile_enabled:
        return
    _sync_security_env()
    repo = SAUserProfileRepo()
    outbox = SAOutboxAdapter()
    iam = ProfileIamClient()
    svc = ProfileService(repo=repo, outbox=outbox, iam=iam, flags=Flags())
    # Attach to the existing DI container for DDD router access
    container = getattr(app.state, "container", None)
    if container is None:
        app.state.container = type("Container", (), {})()  # minimal fallback
        container = app.state.container
    setattr(container, "profile_service", svc)


def include_profile_router(app: FastAPI) -> None:
    if not feature_flags.profile_enabled:
        return
    # Import lazily to ensure env sync is applied first
    from apps.backendDDD.domains.product.profile.api.http import make_router

    app.include_router(make_router())

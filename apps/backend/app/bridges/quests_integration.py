from __future__ import annotations

from fastapi import FastAPI

from apps.backendDDD.domains.product.quests.application.service import QuestService
from app.bridges.quests_repo_adapter import SAQuestsRepo
from app.bridges.tag_catalog_adapter import SATagCatalog
from app.bridges.outbox_adapter import SAOutboxAdapter

try:  # pragma: no cover - environment-dependent import path
    from config.feature_flags import feature_flags  # type: ignore
except ModuleNotFoundError:  # pragma: no cover
    from apps.backend.config.feature_flags import feature_flags  # type: ignore


def wire_quests_service(app: FastAPI) -> None:
    if not getattr(feature_flags, "quests_v2_enabled", True):
        return
    repo = SAQuestsRepo()
    catalog = SATagCatalog()
    outbox = SAOutboxAdapter()
    svc = QuestService(repo=repo, tags=catalog, outbox=outbox)
    container = getattr(app.state, "container", None)
    if container is None:
        app.state.container = type("Container", (), {})()
        container = app.state.container
    setattr(container, "quests_service", svc)


def include_quests_router(app: FastAPI) -> None:
    if not getattr(feature_flags, "quests_v2_enabled", True):
        return
    # Lazy import
    from apps.backendDDD.domains.product.quests.api.http import make_router

    app.include_router(make_router())


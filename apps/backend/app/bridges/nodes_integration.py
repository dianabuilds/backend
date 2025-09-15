from __future__ import annotations

from fastapi import FastAPI

from apps.backendDDD.domains.product.nodes.application.service import NodeService
from app.bridges.nodes_repo_adapter import SANodesRepo
from app.bridges.tag_catalog_adapter import SATagCatalog
from app.bridges.outbox_adapter import SAOutboxAdapter
from app.bridges.tag_usage_projection_adapter import SATagUsageProjection

try:  # pragma: no cover - environment-dependent import path
    from config.feature_flags import feature_flags  # type: ignore
except ModuleNotFoundError:  # pragma: no cover
    from apps.backend.config.feature_flags import feature_flags  # type: ignore


def wire_nodes_service(app: FastAPI) -> None:
    if not getattr(feature_flags, "nodes_v1_enabled", True):
        return
    repo = SANodesRepo()
    catalog = SATagCatalog()
    outbox = SAOutboxAdapter()
    # Projection updates are handled asynchronously via outbox consumer
    svc = NodeService(repo=repo, tags=catalog, outbox=outbox, usage=None)
    container = getattr(app.state, "container", None)
    if container is None:
        app.state.container = type("Container", (), {})()
        container = app.state.container
    setattr(container, "nodes_service", svc)


def include_nodes_router(app: FastAPI) -> None:
    if not getattr(feature_flags, "nodes_v1_enabled", True):
        return
    # Lazy import
    from apps.backendDDD.domains.product.nodes.api.http import make_router

    app.include_router(make_router())

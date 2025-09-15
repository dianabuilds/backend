from __future__ import annotations

from fastapi import FastAPI

from apps.backendDDD.domains.product.navigation.application.service import NavigationService
from app.bridges.navigation_nodes_port_adapter import NodesReadPort

try:  # pragma: no cover
    from config.feature_flags import feature_flags  # type: ignore
except ModuleNotFoundError:  # pragma: no cover
    from apps.backend.config.feature_flags import feature_flags  # type: ignore


def wire_navigation_service(app: FastAPI) -> None:
    if not getattr(feature_flags, "navigation_v2_enabled", True):
        return
    container = getattr(app.state, "container", None)
    if container is None or not hasattr(container, "nodes_service"):
        return
    nodes_port = NodesReadPort(container.nodes_service)
    svc = NavigationService(nodes=nodes_port)
    setattr(container, "navigation_service", svc)


def include_navigation_router(app: FastAPI) -> None:
    if not getattr(feature_flags, "navigation_v2_enabled", True):
        return
    from apps.backendDDD.domains.product.navigation.api.http import make_router

    app.include_router(make_router())


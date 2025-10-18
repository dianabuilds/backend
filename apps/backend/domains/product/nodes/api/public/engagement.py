from __future__ import annotations

from typing import Any

from fastapi import APIRouter, Depends, Query, Request

from apps.backend.infra.security.rate_limits import PUBLIC_RATE_LIMITS
from domains.platform.iam.application.facade import csrf_protect, get_current_user

from .deps import get_engagement_service


def register_engagement_routes(router: APIRouter) -> None:
    service_dep = Depends(get_engagement_service)
    NODES_PUBLIC_RATE_LIMIT = PUBLIC_RATE_LIMITS["nodes"].as_dependencies()

    @router.post(
        "/{node_id}/views",
        dependencies=NODES_PUBLIC_RATE_LIMIT,
    )
    async def register_view(
        node_id: str,
        body: dict[str, Any] | None,
        _req: Request,
        service=service_dep,
        claims=Depends(get_current_user),
        _csrf: None = Depends(csrf_protect),
    ):
        return await service.register_view(node_id, body, claims)

    @router.get("/{node_id}/views")
    async def get_views(
        node_id: str,
        _req: Request,
        service=service_dep,
        limit: int = Query(default=30, ge=1, le=90),
        offset: int = Query(default=0, ge=0),
    ):
        return await service.get_views(node_id, limit=limit, offset=offset)

    @router.post(
        "/{node_id}/reactions/like",
        dependencies=NODES_PUBLIC_RATE_LIMIT,
    )
    async def add_like(
        node_id: str,
        _req: Request,
        service=service_dep,
        claims=Depends(get_current_user),
        _csrf: None = Depends(csrf_protect),
    ):
        return await service.add_like(node_id, claims)

    @router.delete(
        "/{node_id}/reactions/like",
        dependencies=NODES_PUBLIC_RATE_LIMIT,
    )
    async def remove_like(
        node_id: str,
        _req: Request,
        service=service_dep,
        claims=Depends(get_current_user),
        _csrf: None = Depends(csrf_protect),
    ):
        return await service.remove_like(node_id, claims)

    @router.get("/{node_id}/reactions")
    async def get_reactions(
        node_id: str,
        _req: Request,
        service=service_dep,
        claims=Depends(get_current_user),
    ):
        return await service.get_reactions(node_id, claims)

    @router.get("/views")
    async def list_saved_views(
        _req: Request,
        service=service_dep,
        claims=Depends(get_current_user),
    ):
        return await service.list_saved_views(claims)

    @router.post(
        "/views",
        dependencies=NODES_PUBLIC_RATE_LIMIT,
    )
    async def upsert_saved_view(
        body: dict[str, Any],
        _req: Request,
        service=service_dep,
        claims=Depends(get_current_user),
        _csrf: None = Depends(csrf_protect),
    ):
        return await service.upsert_saved_view(body, claims)

    @router.delete(
        "/views/{name}",
        dependencies=NODES_PUBLIC_RATE_LIMIT,
    )
    async def delete_saved_view(
        name: str,
        _req: Request,
        service=service_dep,
        claims=Depends(get_current_user),
        _csrf: None = Depends(csrf_protect),
    ):
        return await service.delete_saved_view(name, claims)

    @router.post(
        "/views/{name}/default",
        dependencies=NODES_PUBLIC_RATE_LIMIT,
    )
    async def set_default_saved_view(
        name: str,
        _req: Request,
        service=service_dep,
        claims=Depends(get_current_user),
        _csrf: None = Depends(csrf_protect),
    ):
        return await service.set_default_saved_view(name, claims)

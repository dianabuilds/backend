from __future__ import annotations

from functools import wraps
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Query, Request

from apps.backend.app.api_gateway.routers import get_container
from domains.platform.iam.application.facade import (
    csrf_protect,
    require_admin,
)
from domains.product.nodes.application.admin_queries import (
    AdminQueryError,
    _extract_actor_id,
    bulk_update_status,
    bulk_update_tags,
    delete_node,
    get_node_engagement,
    list_nodes_admin,
    restore_node,
)


def _wrap_admin_errors(func):
    @wraps(func)
    async def wrapper(*args, **kwargs):
        try:
            return await func(*args, **kwargs)
        except AdminQueryError as exc:
            raise HTTPException(
                status_code=exc.status_code, detail=exc.detail
            ) from exc.__cause__

    return wrapper


def register_nodes_routes(router: APIRouter) -> None:
    @router.get("/list", summary="List nodes for admin")
    @_wrap_admin_errors
    async def list_nodes(
        q: str | None = Query(default=None),
        slug: str | None = Query(default=None, description="Filter by exact slug"),
        tag: str | None = Query(default=None, description="Filter by tag slug"),
        author_id: str | None = Query(
            default=None, description="Filter by author id (UUID)"
        ),
        limit: int = Query(ge=1, le=1000, default=50),
        offset: int = Query(ge=0, default=0),
        status: str | None = Query(default="all"),
        moderation_status: str | None = Query(default=None),
        updated_from: str | None = Query(default=None),
        updated_to: str | None = Query(default=None),
        sort: str | None = Query(default="updated_at"),
        order: str | None = Query(default="desc"),
        _: None = Depends(require_admin),
        container=Depends(get_container),
    ) -> list[dict[str, Any]]:
        return await list_nodes_admin(
            container,
            q=q,
            slug=slug,
            tag=tag,
            author_id=author_id,
            limit=limit,
            offset=offset,
            status=status,
            moderation_status=moderation_status,
            updated_from=updated_from,
            updated_to=updated_to,
            sort=sort,
            order=order,
        )

    @router.get("/{node_id}/engagement", summary="Get node engagement summary")
    @_wrap_admin_errors
    async def get_node_engagement_admin(
        node_id: str,
        _: None = Depends(require_admin),
        container=Depends(get_container),
    ) -> dict[str, Any]:
        return await get_node_engagement(
            container,
            node_identifier=node_id,
        )

    @router.delete("/{node_id}", summary="Admin delete node")
    @_wrap_admin_errors
    async def admin_delete(
        node_id: int,
        request: Request,
        _csrf: None = Depends(csrf_protect),
        _: None = Depends(require_admin),
        container=Depends(get_container),
    ) -> dict[str, Any]:
        actor_id = _extract_actor_id(request)
        return await delete_node(
            container,
            node_id=int(node_id),
            actor_id=actor_id,
        )

    @router.post("/bulk/status", summary="Bulk update node status")
    @_wrap_admin_errors
    async def bulk_status(
        body: dict,
        request: Request,
        _csrf: None = Depends(csrf_protect),
        _: None = Depends(require_admin),
        container=Depends(get_container),
    ) -> dict[str, Any]:
        if not isinstance(body, dict):
            raise HTTPException(status_code=400, detail="invalid_body")
        ids = body.get("ids") or []
        status = body.get("status")
        publish_at = body.get("publish_at")
        unpublish_at = body.get("unpublish_at")
        if not isinstance(ids, list) or not ids:
            raise HTTPException(status_code=400, detail="ids_required")
        if not isinstance(status, str) or not status:
            raise HTTPException(status_code=400, detail="status_required")
        actor_id = _extract_actor_id(request)
        return await bulk_update_status(
            container,
            ids=[int(i) for i in ids],
            status=str(status),
            publish_at=publish_at,
            unpublish_at=unpublish_at,
            actor_id=actor_id,
        )

    @router.post("/bulk/tags", summary="Bulk add/remove tags")
    @_wrap_admin_errors
    async def bulk_tags(
        body: dict,
        request: Request,
        _csrf: None = Depends(csrf_protect),
        _: None = Depends(require_admin),
        container=Depends(get_container),
    ) -> dict[str, Any]:
        if not isinstance(body, dict):
            raise HTTPException(status_code=400, detail="invalid_body")
        ids = body.get("ids") or []
        tags = body.get("tags") or []
        action = str(body.get("action") or "").lower()
        if not isinstance(ids, list) or not ids:
            raise HTTPException(status_code=400, detail="ids_required")
        if not isinstance(tags, list) or not tags:
            raise HTTPException(status_code=400, detail="tags_required")
        actor_id = _extract_actor_id(request)
        return await bulk_update_tags(
            container,
            ids=[int(i) for i in ids],
            tags=tags,
            action=action,
            actor_id=actor_id,
        )

    @router.post("/{node_id}/restore", summary="Restore soft-deleted node")
    @_wrap_admin_errors
    async def restore_node_admin(
        node_id: int,
        request: Request,
        _csrf: None = Depends(csrf_protect),
        _: None = Depends(require_admin),
        container=Depends(get_container),
    ) -> dict[str, Any]:
        actor_id = _extract_actor_id(request)
        return await restore_node(
            container,
            node_id=int(node_id),
            actor_id=actor_id,
        )

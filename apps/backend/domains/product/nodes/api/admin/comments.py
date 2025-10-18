from __future__ import annotations

from functools import wraps
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Query, Request

from apps.backend.app.api_gateway.routers import get_container
from domains.platform.iam.application.facade import csrf_protect, require_admin
from domains.product.nodes.application.admin_queries import (
    AdminQueryError,
    _extract_actor_id,
    delete_comment,
    list_node_comments,
    set_comments_disabled,
    set_comments_lock,
    update_comment_status,
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


def register_comment_routes(router: APIRouter) -> None:
    @router.get("/{node_id}/comments", summary="List node comments for admin")
    @_wrap_admin_errors
    async def list_node_comments_admin(
        node_id: str,
        view: str = Query(default="roots"),
        parent_id: int | None = Query(default=None, alias="parentId"),
        status: list[str] | None = Query(default=None),
        author_id: str | None = Query(default=None, alias="authorId"),
        created_from: str | None = Query(default=None, alias="createdFrom"),
        created_to: str | None = Query(default=None, alias="createdTo"),
        search: str | None = Query(default=None),
        include_deleted: bool = Query(default=True, alias="includeDeleted"),
        limit: int = Query(default=50, ge=1, le=200),
        offset: int = Query(default=0, ge=0),
        order: str = Query(default="desc"),
        _: None = Depends(require_admin),
        container=Depends(get_container),
    ) -> dict[str, Any]:
        return await list_node_comments(
            container,
            node_identifier=node_id,
            view=view,
            parent_id=parent_id,
            statuses=status,
            author_id=author_id,
            created_from=created_from,
            created_to=created_to,
            search=search,
            include_deleted=include_deleted,
            limit=limit,
            offset=offset,
            order=order,
        )

    @router.post("/{node_id}/comments/lock", summary="Lock or unlock node comments")
    @_wrap_admin_errors
    async def set_comments_lock_admin(
        node_id: str,
        request: Request,
        body: dict[str, Any] | None = None,
        _: None = Depends(require_admin),
        _csrf: None = Depends(csrf_protect),
        container=Depends(get_container),
    ) -> dict[str, Any]:
        payload = body or {}
        locked = bool(payload.get("locked"))
        reason = payload.get("reason")
        actor_id = _extract_actor_id(request)
        return await set_comments_lock(
            container,
            node_identifier=node_id,
            locked=locked,
            actor_id=actor_id,
            reason=reason,
        )

    @router.post(
        "/{node_id}/comments/disable", summary="Enable or disable node comments"
    )
    @_wrap_admin_errors
    async def set_comments_disabled_admin(
        node_id: str,
        request: Request,
        body: dict[str, Any] | None = None,
        _: None = Depends(require_admin),
        _csrf: None = Depends(csrf_protect),
        container=Depends(get_container),
    ) -> dict[str, Any]:
        payload = body or {}
        disabled = bool(payload.get("disabled"))
        reason = payload.get("reason")
        actor_id = _extract_actor_id(request)
        return await set_comments_disabled(
            container,
            node_identifier=node_id,
            disabled=disabled,
            actor_id=actor_id,
            reason=reason,
        )

    @router.post(
        "/comments/{comment_id}/status", summary="Update comment status (admin)"
    )
    @_wrap_admin_errors
    async def update_comment_status_admin(
        comment_id: int,
        request: Request,
        body: dict[str, Any],
        _: None = Depends(require_admin),
        _csrf: None = Depends(csrf_protect),
        container=Depends(get_container),
    ) -> dict[str, Any]:
        status_value = body.get("status")
        reason = body.get("reason")
        actor_id = _extract_actor_id(request)
        return await update_comment_status(
            container,
            comment_id=int(comment_id),
            status=status_value,
            actor_id=actor_id,
            reason=reason,
        )

    @router.delete("/comments/{comment_id}", summary="Delete comment (admin)")
    @_wrap_admin_errors
    async def delete_comment_admin(
        comment_id: int,
        request: Request,
        hard: bool = Query(default=False),
        reason: str | None = Query(default=None),
        _: None = Depends(require_admin),
        _csrf: None = Depends(csrf_protect),
        container=Depends(get_container),
    ) -> dict[str, Any]:
        actor_id = _extract_actor_id(request)
        return await delete_comment(
            container,
            comment_id=int(comment_id),
            actor_id=actor_id,
            hard=bool(hard),
            reason=reason,
        )

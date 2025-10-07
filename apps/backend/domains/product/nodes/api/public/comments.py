from __future__ import annotations

from typing import Any

from fastapi import APIRouter, Depends, Query, Request

from domains.platform.iam.security import csrf_protect, get_current_user

from .deps import get_comments_service


def register_comment_routes(router: APIRouter) -> None:
    service_dep = Depends(get_comments_service)

    @router.get("/{node_id}/comments")
    async def list_comments(
        node_id: str,
        _req: Request,
        service=service_dep,
        claims=Depends(get_current_user),
        parent_id: int | None = Query(default=None, alias="parentId"),
        limit: int = Query(default=50, ge=1, le=200),
        offset: int = Query(default=0, ge=0),
        include_deleted: bool = Query(default=False, alias="includeDeleted"),
    ):
        return await service.list_comments(
            node_id,
            parent_comment_id=parent_id,
            limit=limit,
            offset=offset,
            include_deleted=include_deleted,
            claims=claims,
        )

    @router.post("/{node_id}/comments")
    async def create_comment(
        node_id: str,
        body: dict[str, Any],
        _req: Request,
        service=service_dep,
        claims=Depends(get_current_user),
        _csrf: None = Depends(csrf_protect),
    ):
        return await service.create_comment(node_id, body, claims)

    @router.delete("/comments/{comment_id}")
    async def delete_comment(
        comment_id: int,
        _req: Request,
        service=service_dep,
        claims=Depends(get_current_user),
        hard: bool = Query(default=False),
        reason: str | None = Query(default=None),
        _csrf: None = Depends(csrf_protect),
    ):
        return await service.delete_comment(
            comment_id,
            hard=bool(hard),
            reason=reason,
            claims=claims,
        )

    @router.patch("/comments/{comment_id}/status")
    async def update_comment_status(
        comment_id: int,
        body: dict[str, Any],
        _req: Request,
        service=service_dep,
        claims=Depends(get_current_user),
        _csrf: None = Depends(csrf_protect),
    ):
        return await service.update_comment_status(comment_id, body, claims)

    @router.post("/{node_id}/comments/lock")
    async def toggle_comments_lock(
        node_id: str,
        body: dict[str, Any],
        _req: Request,
        service=service_dep,
        claims=Depends(get_current_user),
        _csrf: None = Depends(csrf_protect),
    ):
        return await service.toggle_comments_lock(node_id, body, claims)

    @router.post("/{node_id}/comments/disable")
    async def toggle_comments_disabled(
        node_id: str,
        body: dict[str, Any],
        _req: Request,
        service=service_dep,
        claims=Depends(get_current_user),
        _csrf: None = Depends(csrf_protect),
    ):
        return await service.toggle_comments_disabled(node_id, body, claims)

    @router.post("/{node_id}/comments/ban")
    async def ban_comment_user(
        node_id: str,
        body: dict[str, Any],
        _req: Request,
        service=service_dep,
        claims=Depends(get_current_user),
        _csrf: None = Depends(csrf_protect),
    ):
        return await service.ban_comment_user(node_id, body, claims)

    @router.delete("/{node_id}/comments/ban/{target_user_id}")
    async def unban_comment_user(
        node_id: str,
        target_user_id: str,
        _req: Request,
        service=service_dep,
        claims=Depends(get_current_user),
        _csrf: None = Depends(csrf_protect),
    ):
        return await service.unban_comment_user(node_id, target_user_id, claims)

    @router.get("/{node_id}/comments/bans")
    async def list_comment_bans(
        node_id: str,
        _req: Request,
        service=service_dep,
        claims=Depends(get_current_user),
    ):
        return await service.list_comment_bans(node_id, claims)

from __future__ import annotations

from functools import wraps
from typing import Any

from app.api_gateway.routers import get_container
from fastapi import APIRouter, Depends, HTTPException, Request

from domains.platform.iam.security import require_admin  # type: ignore[import-not-found]
from domains.product.nodes.application.admin_queries import (
    AdminQueryError,
    _extract_actor_id,
    create_comment_ban,
    delete_comment_ban,
    list_comment_bans,
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


def register_comment_ban_routes(router: APIRouter) -> None:
    @router.get("/{node_id}/comment-bans", summary="List comment bans for node")
    @_wrap_admin_errors
    async def list_comment_bans_admin(
        node_id: str,
        _: None = Depends(require_admin),
        container=Depends(get_container),
    ) -> list[dict[str, Any]]:
        return await list_comment_bans(
            container,
            node_identifier=node_id,
        )

    @router.post("/{node_id}/comment-bans", summary="Create comment ban")
    @_wrap_admin_errors
    async def create_comment_ban_admin(
        node_id: str,
        request: Request,
        body: dict[str, Any] | None = None,
        _: None = Depends(require_admin),
        container=Depends(get_container),
    ) -> dict[str, Any]:
        payload = body or {}
        target_user_id = payload.get("target_user_id") or payload.get("targetUserId")
        reason = payload.get("reason")
        actor_id = _extract_actor_id(request)
        return await create_comment_ban(
            container,
            node_identifier=node_id,
            target_user_id=target_user_id,
            actor_id=actor_id,
            reason=reason,
        )

    @router.delete("/{node_id}/comment-bans/{user_id}", summary="Remove comment ban")
    @_wrap_admin_errors
    async def delete_comment_ban_admin(
        node_id: str,
        user_id: str,
        request: Request,
        _: None = Depends(require_admin),
        container=Depends(get_container),
    ) -> dict[str, Any]:
        actor_id = _extract_actor_id(request)
        return await delete_comment_ban(
            container,
            node_identifier=node_id,
            target_user_id=user_id,
            actor_id=actor_id,
        )

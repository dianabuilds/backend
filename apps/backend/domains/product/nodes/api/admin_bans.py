from __future__ import annotations

from functools import wraps
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Request

from apps.backend import get_container
from domains.platform.iam.security import require_admin  # type: ignore[import-not-found]
from domains.product.nodes.application.admin_queries import (
    SYSTEM_ACTOR_ID,
    AdminQueryError,
    _ban_to_dict,
    _emit_admin_activity,
    _ensure_engine,
    _extract_actor_id,
    _resolve_node_id,
)

from ._memory_utils import resolve_memory_node


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
        engine = await _ensure_engine(container)
        if engine is None:
            dto = await resolve_memory_node(container, node_id)
            if dto is None:
                raise HTTPException(status_code=404, detail="not_found")
            resolved_id = int(dto.id)
        else:
            resolved_id = await _resolve_node_id(node_id, container, engine)
        svc = container.nodes_service
        bans = await svc.list_comment_bans(resolved_id)
        return [_ban_to_dict(ban) for ban in bans]

    @router.post("/{node_id}/comment-bans", summary="Create comment ban")
    @_wrap_admin_errors
    async def create_comment_ban_admin(
        node_id: str,
        request: Request,
        body: dict[str, Any] | None = None,
        _: None = Depends(require_admin),
        container=Depends(get_container),
    ) -> dict[str, Any]:
        if not body:
            raise HTTPException(status_code=400, detail="target_user_id_required")
        target_user_id = body.get("target_user_id") or body.get("targetUserId")
        if not target_user_id:
            raise HTTPException(status_code=400, detail="target_user_id_required")
        reason = body.get("reason")
        engine = await _ensure_engine(container)
        if engine is None:
            dto = await resolve_memory_node(container, node_id)
            if dto is None:
                raise HTTPException(status_code=404, detail="not_found")
            resolved_id = int(dto.id)
        else:
            resolved_id = await _resolve_node_id(node_id, container, engine)
        actor_id = _extract_actor_id(request) or SYSTEM_ACTOR_ID
        svc = container.nodes_service
        ban = await svc.ban_comment_user(
            resolved_id,
            target_user_id=str(target_user_id),
            actor_id=actor_id,
            reason=reason,
        )
        await _emit_admin_activity(
            container,
            event="node.comments.user_banned.admin",
            payload={
                "node_id": ban.node_id,
                "target_user_id": ban.target_user_id,
                "reason": reason,
            },
            key=f"node:{ban.node_id}:comments:ban:{ban.target_user_id}:admin",
            event_context={
                "node_id": ban.node_id,
                "target_user_id": ban.target_user_id,
                "source": "admin_comment_ban",
            },
            audit_action="product.nodes.comments.ban",
            audit_actor=actor_id or SYSTEM_ACTOR_ID,
            audit_resource_type="node",
            audit_resource_id=str(ban.node_id),
            audit_reason=reason,
            audit_extra={"target_user_id": ban.target_user_id},
        )
        return _ban_to_dict(ban)

    @router.delete("/{node_id}/comment-bans/{user_id}", summary="Remove comment ban")
    @_wrap_admin_errors
    async def delete_comment_ban_admin(
        node_id: str,
        user_id: str,
        request: Request,
        _: None = Depends(require_admin),
        container=Depends(get_container),
    ) -> dict[str, Any]:
        engine = await _ensure_engine(container)
        if engine is None:
            dto = await resolve_memory_node(container, node_id)
            if dto is None:
                raise HTTPException(status_code=404, detail="not_found")
            resolved_id = int(dto.id)
        else:
            resolved_id = await _resolve_node_id(node_id, container, engine)
        svc = container.nodes_service
        removed = await svc.unban_comment_user(resolved_id, user_id)
        if not removed:
            raise HTTPException(status_code=404, detail="not_found")
        actor_id = _extract_actor_id(request) or SYSTEM_ACTOR_ID
        await _emit_admin_activity(
            container,
            event="node.comments.user_unbanned.admin",
            payload={"node_id": resolved_id, "target_user_id": user_id},
            key=f"node:{resolved_id}:comments:ban:{user_id}:admin",
            event_context={
                "node_id": resolved_id,
                "target_user_id": user_id,
                "source": "admin_comment_unban",
            },
            audit_action="product.nodes.comments.unban",
            audit_actor=actor_id or SYSTEM_ACTOR_ID,
            audit_resource_type="node",
            audit_resource_id=str(resolved_id),
        )
        return {"ok": True}

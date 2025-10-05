from __future__ import annotations

from functools import wraps
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Query, Request

from apps.backend import get_container
from domains.platform.iam.security import require_admin  # type: ignore[import-not-found]
from domains.product.nodes.application.admin_queries import (
    SYSTEM_ACTOR_ID,
    AdminQueryError,
    _comment_dto_to_dict,
    _emit_admin_activity,
    _ensure_engine,
    _extract_actor_id,
    _fetch_comments_data,
    _fetch_engagement_summary,
    _iso,
    _normalize_comment_status_filter,
    _parse_query_datetime,
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


def register_comment_routes(router: APIRouter) -> None:
    @router.get("/{node_id}/comments", summary="List node comments for admin")
    @_wrap_admin_errors
    async def list_node_comments(
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
        statuses = _normalize_comment_status_filter(
            status, include_deleted=include_deleted
        )
        created_from_dt = _parse_query_datetime(created_from, field="created_from")
        created_to_dt = _parse_query_datetime(created_to, field="created_to")
        parent_int: int | None = None
        if parent_id is not None:
            try:
                parent_int = int(parent_id)
            except (TypeError, ValueError):
                raise HTTPException(
                    status_code=400, detail="parent_id_invalid"
                ) from None
        order_norm = (order or "desc").lower()
        if order_norm not in {"asc", "desc"}:
            order_norm = "desc"
        filters_payload = {
            "statuses": statuses,
            "author_id": author_id,
            "created_from": _iso(created_from_dt),
            "created_to": _iso(created_to_dt),
            "search": search,
            "include_deleted": include_deleted,
            "parent_id": str(parent_int) if parent_int is not None else None,
        }
        engine = await _ensure_engine(container)
        if engine is None:
            dto = await resolve_memory_node(container, node_id)
            if dto is None:
                raise HTTPException(status_code=404, detail="not_found")
            svc = container.nodes_service
            comments = await svc.list_comments(
                int(dto.id),
                parent_comment_id=parent_int,
                limit=limit,
                offset=offset,
                include_deleted=include_deleted,
            )
            items = [_comment_dto_to_dict(comment) for comment in comments]
            return {
                "node_id": str(dto.id),
                "view": (view or "roots").lower(),
                "filters": filters_payload,
                "items": items,
                "total": len(items),
                "has_more": False,
            }
        resolved_id = await _resolve_node_id(node_id, container, engine)

        data = await _fetch_comments_data(
            engine,
            node_id=resolved_id,
            view=view,
            parent_id=parent_int,
            statuses=statuses,
            author_id=author_id,
            created_from=created_from_dt,
            created_to=created_to_dt,
            search=search,
            limit=limit,
            offset=offset,
            order=order_norm,
        )
        response = {
            "node_id": str(resolved_id),
            "view": (view or "roots").lower(),
            "filters": filters_payload,
        }
        response.update(data)
        return response

    @router.post("/{node_id}/comments/lock", summary="Lock or unlock node comments")
    @_wrap_admin_errors
    async def set_comments_lock(
        node_id: str,
        request: Request,
        body: dict[str, Any] | None = None,
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
        payload = body or {}
        locked = bool(payload.get("locked"))
        reason = payload.get("reason")
        actor_id = _extract_actor_id(request) or SYSTEM_ACTOR_ID
        svc = container.nodes_service
        if locked:
            await svc.lock_comments(resolved_id, actor_id=actor_id, reason=reason)
        else:
            await svc.unlock_comments(resolved_id, actor_id=actor_id)
        await _emit_admin_activity(
            container,
            event=(
                "node.comments.locked.admin"
                if locked
                else "node.comments.unlocked.admin"
            ),
            payload={"id": resolved_id, "locked": locked, "actor_id": actor_id},
            key=f"node:{resolved_id}:comments:lock",
            event_context={"node_id": resolved_id, "source": "admin_comments_lock"},
            audit_action=(
                "product.nodes.comments.lock"
                if locked
                else "product.nodes.comments.unlock"
            ),
            audit_actor=actor_id or SYSTEM_ACTOR_ID,
            audit_resource_type="node",
            audit_resource_id=str(resolved_id),
            audit_reason=reason,
        )
        comments_summary = None
        if engine is not None:
            summary = await _fetch_engagement_summary(engine, resolved_id)
            comments_summary = summary["comments"]
        return {
            "locked": locked,
            "comments": comments_summary,
        }

    @router.post(
        "/{node_id}/comments/disable", summary="Enable or disable node comments"
    )
    @_wrap_admin_errors
    async def set_comments_disabled(
        node_id: str,
        request: Request,
        body: dict[str, Any] | None = None,
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
        payload = body or {}
        disabled = bool(payload.get("disabled"))
        reason = payload.get("reason")
        actor_id = _extract_actor_id(request)
        svc = container.nodes_service
        if disabled:
            await svc.disable_comments(resolved_id, actor_id=actor_id, reason=reason)
        else:
            await svc.enable_comments(resolved_id, actor_id=actor_id, reason=reason)
        await _emit_admin_activity(
            container,
            event=(
                "node.comments.disabled.admin"
                if disabled
                else "node.comments.enabled.admin"
            ),
            payload={"id": resolved_id, "disabled": disabled, "actor_id": actor_id},
            key=f"node:{resolved_id}:comments:disable",
            event_context={"node_id": resolved_id, "source": "admin_comments_disable"},
            audit_action=(
                "product.nodes.comments.disable"
                if disabled
                else "product.nodes.comments.enable"
            ),
            audit_actor=actor_id or SYSTEM_ACTOR_ID,
            audit_resource_type="node",
            audit_resource_id=str(resolved_id),
            audit_reason=reason,
        )
        comments_summary = None
        if engine is not None:
            summary = await _fetch_engagement_summary(engine, resolved_id)
            comments_summary = summary["comments"]
        return {
            "disabled": disabled,
            "comments": comments_summary,
        }

    @router.post(
        "/comments/{comment_id}/status", summary="Update comment status (admin)"
    )
    @_wrap_admin_errors
    async def update_comment_status_admin(
        comment_id: int,
        request: Request,
        body: dict[str, Any],
        _: None = Depends(require_admin),
        container=Depends(get_container),
    ) -> dict[str, Any]:
        status_value = body.get("status")
        if not status_value:
            raise HTTPException(status_code=400, detail="status_required")
        reason = body.get("reason")
        actor_id = _extract_actor_id(request)
        svc = container.nodes_service
        try:
            updated = await svc.update_comment_status(
                int(comment_id), status=status_value, actor_id=actor_id, reason=reason
            )
        except ValueError as exc:  # noqa: PERF203
            detail = str(exc) or "invalid_status"
            if detail == "comment_not_found":
                raise HTTPException(status_code=404, detail="not_found") from None
            raise HTTPException(status_code=400, detail=detail) from None
        engine = await _ensure_engine(container)
        comments_summary = None
        if engine is not None:
            summary = await _fetch_engagement_summary(engine, updated.node_id)
            comments_summary = summary["comments"]
        await _emit_admin_activity(
            container,
            event="node.comment.status.admin",
            payload={
                "id": updated.id,
                "node_id": updated.node_id,
                "status": updated.status,
            },
            key=f"node:{updated.node_id}:comment:{updated.id}:status:admin",
            event_context={
                "node_id": updated.node_id,
                "comment_id": updated.id,
                "source": "admin_comment_status",
            },
            audit_action="product.nodes.comments.status",
            audit_actor=actor_id or SYSTEM_ACTOR_ID,
            audit_resource_type="comment",
            audit_resource_id=str(updated.id),
            audit_reason=reason,
            audit_extra={"status": updated.status},
        )
        response: dict[str, Any] = {"comment": _comment_dto_to_dict(updated)}
        if comments_summary is not None:
            response["comments"] = comments_summary
        return response

    @router.delete("/comments/{comment_id}", summary="Delete comment (admin)")
    @_wrap_admin_errors
    async def delete_comment_admin(
        comment_id: int,
        request: Request,
        hard: bool = Query(default=False),
        reason: str | None = Query(default=None),
        _: None = Depends(require_admin),
        container=Depends(get_container),
    ) -> dict[str, Any]:
        svc = container.nodes_service
        actor_id = _extract_actor_id(request) or SYSTEM_ACTOR_ID
        comment = await svc.get_comment(int(comment_id))
        if comment is None:
            raise HTTPException(status_code=404, detail="not_found")
        removed = await svc.delete_comment(
            int(comment_id), actor_id=actor_id, hard=bool(hard), reason=reason
        )
        if not removed:
            raise HTTPException(status_code=404, detail="not_found")
        await _emit_admin_activity(
            container,
            event="node.comment.deleted.admin",
            payload={
                "id": comment.id,
                "node_id": comment.node_id,
                "hard": bool(hard),
                "actor_id": actor_id,
            },
            key=f"node:{comment.node_id}:comment:{comment.id}:delete",
            event_context={
                "node_id": comment.node_id,
                "comment_id": comment.id,
                "source": "admin_comment_delete",
            },
            audit_action="product.nodes.comments.delete",
            audit_actor=actor_id or SYSTEM_ACTOR_ID,
            audit_resource_type="comment",
            audit_resource_id=str(comment.id),
            audit_reason=reason,
        )
        engine = await _ensure_engine(container)
        response: dict[str, Any] = {"ok": True}
        if engine is not None:
            summary = await _fetch_engagement_summary(engine, comment.node_id)
            response["comments"] = summary["comments"]
        return response

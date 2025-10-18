from __future__ import annotations

from functools import wraps
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Request

from apps.backend.app.api_gateway.routers import get_container
from domains.platform.iam.application.facade import (
    csrf_protect,
    get_current_user,
    require_admin,
)
from domains.product.nodes.application.admin_queries import (
    AdminQueryError,
    _extract_actor_id,
    apply_moderation_decision,
    get_moderation_detail,
    logger,
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


def register_moderation_routes(router: APIRouter) -> None:
    @router.get("/{node_id}/moderation", summary="Get moderation detail for a node")
    @_wrap_admin_errors
    async def get_node_moderation(
        node_id: str,
        _: None = Depends(require_admin),
        container=Depends(get_container),
    ):
        return await get_moderation_detail(
            container,
            node_identifier=node_id,
        )

    @router.post(
        "/{node_id}/moderation/decision",
        summary="Apply moderation decision",
        dependencies=[Depends(csrf_protect)],
    )
    @_wrap_admin_errors
    async def decide_node_moderation(
        node_id: str,
        body: dict[str, Any],
        request: Request,
        _: None = Depends(require_admin),
        container=Depends(get_container),
    ):
        actor_id = _extract_actor_id(request)
        if not actor_id:
            try:
                claims = await get_current_user(request)
            except HTTPException:
                actor_id = None
            except RuntimeError as exc:
                logger.debug(
                    "nodes_admin_actor_claims_failed",
                    extra={"path": request.url.path},
                    exc_info=exc,
                )
                actor_id = None
            else:
                actor_candidate = str(claims.get("sub") or "")
                actor_id = actor_candidate or None
        if not actor_id:
            actor_id = "admin"
        return await apply_moderation_decision(
            container,
            node_identifier=node_id,
            payload=body,
            actor_id=actor_id,
        )

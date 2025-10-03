from __future__ import annotations

import json
from datetime import UTC, datetime
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy import text
from sqlalchemy.exc import SQLAlchemyError

from apps.backend import get_container
from domains.platform.iam.security import (  # type: ignore[import-not-found]
    csrf_protect,
    get_current_user,
    require_admin,
)

from .admin_common import (
    _DECISION_STATUS_MAP,
    SYSTEM_ACTOR_ID,
    _decision_to_status,
    _emit_admin_activity,
    _ensure_engine,
    _extract_actor_id,
    _fetch_moderation_detail,
    _iso,
    _resolve_node_id,
    logger,
)


def register_moderation_routes(router: APIRouter) -> None:
    @router.get("/{node_id}/moderation", summary="Get moderation detail for a node")
    async def get_node_moderation(
        node_id: str,
        _: None = Depends(require_admin),
        container=Depends(get_container),
    ):
        eng = await _ensure_engine(container)
        if eng is None:
            raise HTTPException(status_code=500, detail="no_engine")
        node_pk = await _resolve_node_id(node_id, container, eng)
        detail = await _fetch_moderation_detail(eng, node_pk)
        if detail is None:
            raise HTTPException(status_code=404, detail="not_found")
        return detail

    @router.post(
        "/{node_id}/moderation/decision",
        summary="Apply moderation decision",
        dependencies=[Depends(csrf_protect)],
    )
    async def decide_node_moderation(
        node_id: str,
        body: dict[str, Any],
        request: Request,
        _: None = Depends(require_admin),
        container=Depends(get_container),
    ):
        if not isinstance(body, dict):
            raise HTTPException(status_code=400, detail="invalid_body")
        eng = await _ensure_engine(container)
        if eng is None:
            raise HTTPException(status_code=500, detail="no_engine")
        node_pk = await _resolve_node_id(node_id, container, eng)
        action = str(body.get("action") or "").strip().lower()
        if action not in _DECISION_STATUS_MAP:
            raise HTTPException(status_code=400, detail="action_invalid")
        reason_raw = body.get("reason")
        if reason_raw is not None and not isinstance(reason_raw, str):
            raise HTTPException(status_code=400, detail="reason_invalid")
        reason = reason_raw.strip() if isinstance(reason_raw, str) and reason_raw.strip() else None
        moderation_status = _decision_to_status(action)
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
                actor_id = str(claims.get("sub") or "") or None
        if not actor_id:
            actor_id = "admin"
        payload_extra = {k: v for k, v in body.items() if k not in {"action", "reason"}}
        payload_extra.update(
            {
                "action": action,
                "reason": reason,
                "status": moderation_status,
                "actor": actor_id,
            }
        )
        decided_at = datetime.now(UTC)
        try:
            payload_json = json.dumps(payload_extra, default=str)
        except (TypeError, ValueError) as exc:
            logger.warning(
                "nodes_admin_payload_serialize_failed",
                extra={"node_id": node_pk},
                exc_info=exc,
            )
            payload_json = "{}"
        insert_params = {
            "node_id": node_pk,
            "action": action,
            "status": moderation_status,
            "reason": reason,
            "actor_id": actor_id,
            "decided_at": decided_at,
            "payload": payload_json,
        }
        node_update_fields = ["moderation_status", "moderation_status_updated_at"]
        status_override: str | None = None
        make_private = False
        if action == "hide":
            status_override = "archived"
            make_private = True
        elif action == "delete":
            status_override = "deleted"
            make_private = True
        try:
            async with eng.begin() as conn:
                exists = (
                    await conn.execute(
                        text("SELECT 1 FROM nodes WHERE id = :node_id"),
                        {"node_id": node_pk},
                    )
                ).first()
                if exists is None:
                    raise HTTPException(status_code=404, detail="not_found")
                await conn.execute(
                    text(
                        "INSERT INTO node_moderation_history (node_id, action, status, reason, actor_id, decided_at, payload) "
                        "VALUES (:node_id, :action, :status, :reason, :actor_id, :decided_at, CAST(:payload AS jsonb))"
                    ),
                    insert_params,
                )
                update_clauses = [
                    "moderation_status = :status",
                    "moderation_status_updated_at = :decided_at",
                    "updated_at = now()",
                ]
                update_params = {
                    "node_id": node_pk,
                    "status": moderation_status,
                    "decided_at": decided_at,
                }
                if status_override:
                    update_clauses.append("status = :node_status")
                    update_params["node_status"] = status_override
                    node_update_fields.append("status")
                if make_private:
                    update_clauses.append("is_public = false")
                    node_update_fields.append("is_public")
                await conn.execute(
                    text(f"UPDATE nodes SET {', '.join(update_clauses)} WHERE id = :node_id"),
                    update_params,
                )
        except HTTPException:
            raise
        except SQLAlchemyError as exc:
            logger.error(
                "nodes_admin_moderation_update_failed",
                extra={"node_id": node_pk},
                exc_info=exc,
            )
            raise HTTPException(status_code=500, detail="moderation_update_failed") from None
        detail = await _fetch_moderation_detail(eng, node_pk)
        event_payload = {
            "id": node_pk,
            "action": action,
            "status": moderation_status,
            "reason": reason,
            "actor_id": actor_id,
            "decided_at": _iso(decided_at),
        }
        audit_extra = {
            "action": action,
            "status": moderation_status,
            "reason": reason,
            "payload": payload_extra,
        }
        await _emit_admin_activity(
            container,
            event="node.moderation.decision.v1",
            payload=event_payload,
            key=f"node:{node_pk}:moderation",
            event_context={
                "node_id": node_pk,
                "action": action,
                "status": moderation_status,
            },
            audit_action="product.nodes.moderation.decision",
            audit_actor=actor_id or SYSTEM_ACTOR_ID,
            audit_resource_type="node",
            audit_resource_id=str(node_pk),
            audit_reason=reason,
            audit_extra=audit_extra,
        )
        await _emit_admin_activity(
            container,
            event="node.updated.v1",
            payload={"id": node_pk, "fields": node_update_fields},
            key=f"node:{node_pk}",
            event_context={"node_id": node_pk, "fields": node_update_fields},
        )
        return detail or {"ok": True, "status": moderation_status}

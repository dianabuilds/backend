from __future__ import annotations

import json
from datetime import UTC, datetime
from functools import wraps
from typing import Any, TypedDict, cast

from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy import text
from sqlalchemy.exc import SQLAlchemyError

from apps.backend import get_container
from domains.platform.iam.security import (  # type: ignore[import-not-found]
    csrf_protect,
    get_current_user,
    require_admin,
)
from domains.product.nodes.application.admin_queries import (
    _DECISION_STATUS_MAP,
    SYSTEM_ACTOR_ID,
    AdminQueryError,
    _decision_to_status,
    _emit_admin_activity,
    _ensure_engine,
    _extract_actor_id,
    _fetch_moderation_detail,
    _iso,
    _resolve_node_id,
    logger,
)

from ._memory_utils import resolve_memory_node


class ModerationHistoryEntry(TypedDict, total=False):
    action: str
    status: str
    reason: str | None
    actor: str | None
    decided_at: str | None


class ModerationMemory(TypedDict):
    status: dict[str, str]
    updated_at: dict[str, str | None]
    history: dict[str, list[ModerationHistoryEntry]]


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


def _get_moderation_memory(container) -> ModerationMemory:
    store = getattr(container, "_moderation_memory", None)
    if not isinstance(store, dict):
        store = {"status": {}, "updated_at": {}, "history": {}}
    else:
        status = dict(store.get("status", {}))
        updated = dict(store.get("updated_at", {}))
        history = dict(store.get("history", {}))
        store = {"status": status, "updated_at": updated, "history": history}
    container._moderation_memory = store
    return cast(ModerationMemory, store)


async def _memory_moderation_detail(container, node_ref: str) -> dict[str, Any] | None:
    dto = await resolve_memory_node(container, node_ref)
    if dto is None:
        return None
    service = container.nodes_service
    view = service._to_view(dto)
    store = _get_moderation_memory(container)
    key = str(dto.id)
    status = store["status"].setdefault(key, "pending")
    updated_at = store["updated_at"].get(key)
    history_entries = store["history"].get(key)
    history = list(history_entries) if history_entries else []
    return {
        "id": str(dto.id),
        "type": "node",
        "author_id": view.author_id,
        "preview": view.title,
        "status": status,
        "moderation_history": history,
        "meta": {
            "node_status": view.status,
            "moderation_status": status,
            "moderation_status_updated_at": updated_at,
            "slug": view.slug,
            "is_public": view.is_public,
        },
        "reports": [],
    }


async def _apply_moderation_decision_memory(
    container,
    *,
    node_id: int,
    action: str,
    moderation_status: str,
    reason: str | None,
    actor_id: str | None,
    decided_at: datetime,
    status_override: str | None,
    make_private: bool,
) -> tuple[dict[str, Any] | None, list[str]]:
    dto = await resolve_memory_node(container, str(node_id))
    if dto is None:
        raise HTTPException(status_code=404, detail="not_found")
    node_update_fields = ["moderation_status", "moderation_status_updated_at"]
    update_kwargs: dict[str, Any] = {}
    if status_override:
        update_kwargs["status"] = status_override
        node_update_fields.append("status")
    if make_private:
        update_kwargs["is_public"] = False
        if "status" not in node_update_fields:
            node_update_fields.append("is_public")
    if update_kwargs:
        await container.nodes_service.update(int(dto.id), **update_kwargs)
    store = _get_moderation_memory(container)
    key = str(dto.id)
    decided_iso = _iso(decided_at)
    history_entry: ModerationHistoryEntry = {
        "action": action,
        "status": moderation_status,
        "reason": reason,
        "actor": actor_id,
        "decided_at": decided_iso,
    }
    history_list: list[ModerationHistoryEntry] | None = store["history"].get(key)
    if not isinstance(history_list, list):
        history_list = []
        store["history"][key] = history_list
    history_list.insert(0, history_entry)
    store["status"][key] = moderation_status
    store["updated_at"][key] = decided_iso
    detail = await _memory_moderation_detail(container, str(dto.id))
    return detail, node_update_fields


def register_moderation_routes(router: APIRouter) -> None:
    @router.get("/{node_id}/moderation", summary="Get moderation detail for a node")
    @_wrap_admin_errors
    async def get_node_moderation(
        node_id: str,
        _: None = Depends(require_admin),
        container=Depends(get_container),
    ):
        eng = await _ensure_engine(container)
        if eng is None:
            detail = await _memory_moderation_detail(container, node_id)
            if detail is None:
                raise HTTPException(status_code=404, detail="not_found")
            return detail
        node_pk = await _resolve_node_id(node_id, container, eng)
        detail = await _fetch_moderation_detail(eng, node_pk)
        if detail is None:
            detail = await _memory_moderation_detail(container, str(node_pk))
        if detail is None:
            detail = await _memory_moderation_detail(container, str(node_pk))
            if detail is None:
                raise HTTPException(status_code=404, detail="not_found")
        return detail

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
        if not isinstance(body, dict):
            raise HTTPException(status_code=400, detail="invalid_body")
        eng = await _ensure_engine(container)
        if eng is None:
            dto = await resolve_memory_node(container, node_id)
            if dto is None:
                raise HTTPException(status_code=404, detail="not_found")
            node_pk = int(dto.id)
        else:
            node_pk = await _resolve_node_id(node_id, container, eng)
        action = str(body.get("action") or "").strip().lower()
        if action not in _DECISION_STATUS_MAP:
            raise HTTPException(status_code=400, detail="action_invalid")
        reason_raw = body.get("reason")
        if reason_raw is not None and not isinstance(reason_raw, str):
            raise HTTPException(status_code=400, detail="reason_invalid")
        reason = (
            reason_raw.strip()
            if isinstance(reason_raw, str) and reason_raw.strip()
            else None
        )
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
        if eng is None:
            detail, node_update_fields = await _apply_moderation_decision_memory(
                container,
                node_id=int(node_pk),
                action=action,
                moderation_status=moderation_status,
                reason=reason,
                actor_id=actor_id,
                decided_at=decided_at,
                status_override=status_override,
                make_private=make_private,
            )
        else:
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
                        text(
                            f"UPDATE nodes SET {', '.join(update_clauses)} WHERE id = :node_id"
                        ),
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
                raise HTTPException(
                    status_code=500, detail="moderation_update_failed"
                ) from None
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

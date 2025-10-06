"""Use-case facade for administrative node operations."""

from __future__ import annotations

import json
from collections.abc import Iterable
from datetime import UTC, datetime
from typing import Any, TypedDict, cast

from sqlalchemy import text
from sqlalchemy.exc import SQLAlchemyError

from domains.product.nodes.adapters.memory.utils import (
    resolve_memory_node as _resolve_memory_node,
)

from .commands import (
    SYSTEM_ACTOR_ID,
    _emit_admin_activity,
)
from .commands import (
    logger as _base_logger,
)
from .exceptions import AdminQueryError
from .presenter import (
    _DECISION_STATUS_MAP,
    _analytics_to_csv,
    _ban_to_dict,
    _comment_dto_to_dict,
    _decision_to_status,
    _iso,
    _normalize_comment_status_filter,
    _normalize_moderation_status,
)
from .queries import (
    _ensure_engine,
    _fetch_analytics,
    _fetch_comments_data,
    _fetch_engagement_summary,
    _fetch_moderation_detail,
    _parse_query_datetime,
    _resolve_node_id,
)

logger = _base_logger

DEV_BLOG_TAG = "dev-blog"


def _normalize_order(order: str | None) -> str:
    value = (order or "desc").lower()
    return value if value in {"asc", "desc"} else "desc"


async def _get_engine_and_node_id(container, node_ref: Any):
    engine = await _ensure_engine(container)
    if engine is None:
        dto = await _resolve_memory_node(container, node_ref)
        if dto is None:
            raise AdminQueryError(404, "not_found")
        return None, int(dto.id), dto
    resolved_id = await _resolve_node_id(node_ref, container, engine)
    return engine, resolved_id, None


async def fetch_node_analytics(
    container,
    *,
    node_identifier: str,
    start: str | None,
    end: str | None,
    limit: int,
) -> dict[str, Any] | None:
    """Return analytics payload when SQL backend is available.

    Returns dict with ``node_id``/``payload``/normalized ``start``/``end``
    (UTC ISO) or ``None`` when SQL backend cannot be used.
    """

    engine = await _ensure_engine(container)
    if engine is None:
        return None
    try:
        start_dt = _parse_query_datetime(start, field="start")
        end_dt = _parse_query_datetime(end, field="end")
        resolved_id = await _resolve_node_id(node_identifier, container, engine)
        payload = await _fetch_analytics(
            engine,
            node_id=resolved_id,
            start=start_dt,
            end=end_dt,
            limit=limit,
        )
        return {
            "node_id": resolved_id,
            "payload": payload,
            "start": start_dt.isoformat().replace("+00:00", "Z") if start_dt else None,
            "end": end_dt.isoformat().replace("+00:00", "Z") if end_dt else None,
        }
    except AdminQueryError:
        raise
    except Exception as exc:  # noqa: BLE001
        logger.warning(
            "nodes_admin_fetch_analytics_failed",
            extra={"node_identifier": node_identifier},
            exc_info=exc,
        )
        return None


def build_analytics_csv(payload: dict[str, Any]) -> str:
    """Serialize analytics payload to CSV."""

    return _analytics_to_csv(payload)


async def list_node_comments(
    container,
    *,
    node_identifier: str,
    view: str,
    parent_id: Any,
    statuses: Iterable[str] | None,
    author_id: str | None,
    created_from: str | None,
    created_to: str | None,
    search: str | None,
    include_deleted: bool,
    limit: int,
    offset: int,
    order: str,
) -> dict[str, Any]:
    normalized_statuses = _normalize_comment_status_filter(
        statuses, include_deleted=include_deleted
    )
    created_from_dt = _parse_query_datetime(created_from, field="created_from")
    created_to_dt = _parse_query_datetime(created_to, field="created_to")
    parent_int: int | None = None
    if parent_id is not None:
        try:
            parent_int = int(parent_id)
        except (TypeError, ValueError):
            raise AdminQueryError(400, "parent_id_invalid") from None
    order_norm = _normalize_order(order)
    filters_payload = {
        "statuses": list(normalized_statuses),
        "author_id": author_id,
        "created_from": _iso(created_from_dt),
        "created_to": _iso(created_to_dt),
        "search": search,
        "include_deleted": include_deleted,
        "parent_id": str(parent_int) if parent_int is not None else None,
    }

    engine, resolved_id, dto = await _get_engine_and_node_id(container, node_identifier)

    if engine is None:
        service = getattr(container, "nodes_service", None)
        if service is None:
            raise AdminQueryError(404, "not_found")
        comments = await service.list_comments(
            resolved_id,
            parent_comment_id=parent_int,
            limit=limit,
            offset=offset,
            include_deleted=include_deleted,
        )
        items = [_comment_dto_to_dict(comment) for comment in comments]
        return {
            "node_id": str(resolved_id),
            "view": (view or "roots").lower(),
            "filters": filters_payload,
            "items": items,
            "summary": None,
            "total": len(items),
            "limit": limit,
            "offset": offset,
            "has_more": False,
        }

    data = await _fetch_comments_data(
        engine,
        node_id=resolved_id,
        view=view,
        parent_id=parent_int,
        statuses=list(normalized_statuses),
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


async def list_comment_bans(
    container,
    *,
    node_identifier: str,
) -> list[dict[str, Any]]:
    engine, resolved_id, _dto = await _get_engine_and_node_id(
        container, node_identifier
    )
    svc = getattr(container, "nodes_service", None)
    if svc is None:
        raise AdminQueryError(500, "service_unavailable")
    bans = await svc.list_comment_bans(resolved_id)
    return [_ban_to_dict(ban) for ban in bans]


async def create_comment_ban(
    container,
    *,
    node_identifier: str,
    target_user_id: str | None,
    actor_id: str | None,
    reason: str | None,
) -> dict[str, Any]:
    if not target_user_id:
        raise AdminQueryError(400, "target_user_id_required")
    engine, resolved_id, _dto = await _get_engine_and_node_id(
        container, node_identifier
    )
    svc = getattr(container, "nodes_service", None)
    if svc is None:
        raise AdminQueryError(500, "service_unavailable")
    actor = actor_id or SYSTEM_ACTOR_ID
    ban = await svc.ban_comment_user(
        resolved_id,
        target_user_id=str(target_user_id),
        actor_id=actor,
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
        audit_actor=actor,
        audit_resource_type="node",
        audit_resource_id=str(ban.node_id),
        audit_reason=reason,
        audit_extra={"target_user_id": ban.target_user_id},
    )
    return _ban_to_dict(ban)


async def delete_comment_ban(
    container,
    *,
    node_identifier: str,
    target_user_id: str,
    actor_id: str | None,
) -> dict[str, Any]:
    if not target_user_id:
        raise AdminQueryError(400, "target_user_id_required")
    engine, resolved_id, _dto = await _get_engine_and_node_id(
        container, node_identifier
    )
    svc = getattr(container, "nodes_service", None)
    if svc is None:
        raise AdminQueryError(500, "service_unavailable")
    removed = await svc.unban_comment_user(resolved_id, target_user_id)
    if not removed:
        raise AdminQueryError(404, "not_found")
    actor = actor_id or SYSTEM_ACTOR_ID
    await _emit_admin_activity(
        container,
        event="node.comments.user_unbanned.admin",
        payload={"node_id": resolved_id, "target_user_id": target_user_id},
        key=f"node:{resolved_id}:comments:ban:{target_user_id}:admin",
        event_context={
            "node_id": resolved_id,
            "target_user_id": target_user_id,
            "source": "admin_comment_unban",
        },
        audit_action="product.nodes.comments.unban",
        audit_actor=actor,
        audit_resource_type="node",
        audit_resource_id=str(resolved_id),
    )
    return {"ok": True}


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
    dto = await _resolve_memory_node(container, node_ref)
    if dto is None:
        return None
    service = getattr(container, "nodes_service", None)
    if service is None:
        return None
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
    dto = await _resolve_memory_node(container, str(node_id))
    if dto is None:
        raise AdminQueryError(404, "not_found")
    service = getattr(container, "nodes_service", None)
    if service is None:
        raise AdminQueryError(500, "service_unavailable")
    node_update_fields = ["moderation_status", "moderation_status_updated_at"]
    update_kwargs: dict[str, Any] = {}
    if status_override:
        update_kwargs["status"] = status_override
        node_update_fields.append("status")
    if make_private:
        update_kwargs["is_public"] = False
        if "is_public" not in node_update_fields:
            node_update_fields.append("is_public")
    if update_kwargs:
        await service.update(int(dto.id), **update_kwargs)
    store = _get_moderation_memory(container)
    key = str(dto.id)
    store["status"][key] = moderation_status
    store["updated_at"][key] = _iso(decided_at)
    history = store["history"].setdefault(key, [])
    history.insert(
        0,
        {
            "action": action,
            "status": moderation_status,
            "reason": reason,
            "actor": actor_id,
            "decided_at": _iso(decided_at),
        },
    )
    detail = await _memory_moderation_detail(container, str(dto.id))
    return detail, node_update_fields


async def get_moderation_detail(
    container,
    *,
    node_identifier: str,
) -> dict[str, Any]:
    engine, resolved_id, _dto = await _get_engine_and_node_id(
        container, node_identifier
    )
    if engine is None:
        detail = await _memory_moderation_detail(container, node_identifier)
        if detail is None:
            raise AdminQueryError(404, "not_found")
        return detail
    detail = await _fetch_moderation_detail(engine, resolved_id)
    if detail is None:
        detail = await _memory_moderation_detail(container, str(resolved_id))
        if detail is None:
            raise AdminQueryError(404, "not_found")
    return detail


async def apply_moderation_decision(
    container,
    *,
    node_identifier: str,
    payload: dict[str, Any],
    actor_id: str | None,
) -> dict[str, Any]:
    if not isinstance(payload, dict):
        raise AdminQueryError(400, "invalid_body")
    action = str(payload.get("action") or "").strip().lower()
    if action not in _DECISION_STATUS_MAP:
        raise AdminQueryError(400, "action_invalid")
    reason_raw = payload.get("reason")
    if reason_raw is not None and not isinstance(reason_raw, str):
        raise AdminQueryError(400, "reason_invalid")
    reason = (
        reason_raw.strip()
        if isinstance(reason_raw, str) and reason_raw.strip()
        else None
    )
    moderation_status = _decision_to_status(action)
    actor = actor_id or SYSTEM_ACTOR_ID
    payload_extra = {k: v for k, v in payload.items() if k not in {"action", "reason"}}
    payload_extra.update(
        {
            "action": action,
            "reason": reason,
            "status": moderation_status,
            "actor": actor,
        }
    )
    engine, resolved_id, _dto = await _get_engine_and_node_id(
        container, node_identifier
    )
    decided_at = datetime.now(UTC)
    try:
        payload_json = json.dumps(payload_extra, default=str)
    except (TypeError, ValueError) as exc:
        logger.warning(
            "nodes_admin_payload_serialize_failed",
            extra={"node_id": resolved_id},
            exc_info=exc,
        )
        payload_json = "{}"
    insert_params = {
        "node_id": resolved_id,
        "action": action,
        "status": moderation_status,
        "reason": reason,
        "actor_id": actor,
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
    if engine is None:
        detail, node_update_fields = await _apply_moderation_decision_memory(
            container,
            node_id=resolved_id,
            action=action,
            moderation_status=moderation_status,
            reason=reason,
            actor_id=actor,
            decided_at=decided_at,
            status_override=status_override,
            make_private=make_private,
        )
    else:
        try:
            async with engine.begin() as conn:
                exists = (
                    await conn.execute(
                        text("SELECT 1 FROM nodes WHERE id = :node_id"),
                        {"node_id": resolved_id},
                    )
                ).first()
                if exists is None:
                    raise AdminQueryError(404, "not_found")
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
                    "node_id": resolved_id,
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
        except AdminQueryError:
            raise
        except SQLAlchemyError as exc:
            logger.error(
                "nodes_admin_moderation_update_failed",
                extra={"node_id": resolved_id},
                exc_info=exc,
            )
            raise AdminQueryError(500, "moderation_update_failed") from None
        detail = await _fetch_moderation_detail(engine, resolved_id)
    event_payload = {
        "id": resolved_id,
        "action": action,
        "status": moderation_status,
        "reason": reason,
        "actor_id": actor,
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
        key=f"node:{resolved_id}:moderation",
        event_context={
            "node_id": resolved_id,
            "action": action,
            "status": moderation_status,
        },
        audit_action="product.nodes.moderation.decision",
        audit_actor=actor,
        audit_resource_type="node",
        audit_resource_id=str(resolved_id),
        audit_reason=reason,
        audit_extra=audit_extra,
    )
    await _emit_admin_activity(
        container,
        event="node.updated.v1",
        payload={"id": resolved_id, "fields": node_update_fields},
        key=f"node:{resolved_id}",
        event_context={"node_id": resolved_id, "fields": node_update_fields},
    )
    return detail or {"ok": True, "status": moderation_status}


async def set_comments_lock(
    container,
    *,
    node_identifier: str,
    locked: bool,
    actor_id: str | None,
    reason: str | None,
) -> dict[str, Any]:
    engine, resolved_id, _dto = await _get_engine_and_node_id(
        container, node_identifier
    )
    actor = actor_id or SYSTEM_ACTOR_ID
    svc = container.nodes_service
    if locked:
        await svc.lock_comments(resolved_id, actor_id=actor, reason=reason)
    else:
        await svc.unlock_comments(resolved_id, actor_id=actor)
    await _emit_admin_activity(
        container,
        event=(
            "node.comments.locked.admin" if locked else "node.comments.unlocked.admin"
        ),
        payload={"id": resolved_id, "locked": locked, "actor_id": actor},
        key=f"node:{resolved_id}:comments:lock",
        event_context={"node_id": resolved_id, "source": "admin_comments_lock"},
        audit_action=(
            "product.nodes.comments.lock" if locked else "product.nodes.comments.unlock"
        ),
        audit_actor=actor,
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


async def set_comments_disabled(
    container,
    *,
    node_identifier: str,
    disabled: bool,
    actor_id: str | None,
    reason: str | None,
) -> dict[str, Any]:
    engine, resolved_id, _dto = await _get_engine_and_node_id(
        container, node_identifier
    )
    actor = actor_id or SYSTEM_ACTOR_ID
    svc = container.nodes_service
    if disabled:
        await svc.disable_comments(resolved_id, actor_id=actor, reason=reason)
    else:
        await svc.enable_comments(resolved_id, actor_id=actor)
    await _emit_admin_activity(
        container,
        event=(
            "node.comments.disabled.admin"
            if disabled
            else "node.comments.enabled.admin"
        ),
        payload={"id": resolved_id, "disabled": disabled, "actor_id": actor},
        key=f"node:{resolved_id}:comments:disable",
        event_context={"node_id": resolved_id, "source": "admin_comments_disable"},
        audit_action=(
            "product.nodes.comments.disable"
            if disabled
            else "product.nodes.comments.enable"
        ),
        audit_actor=actor,
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


async def update_comment_status(
    container,
    *,
    comment_id: int,
    status: str | None,
    actor_id: str | None,
    reason: str | None,
) -> dict[str, Any]:
    if not status:
        raise AdminQueryError(400, "status_required")
    actor = actor_id or SYSTEM_ACTOR_ID
    svc = container.nodes_service
    try:
        updated = await svc.update_comment_status(
            int(comment_id), status=status, actor_id=actor, reason=reason
        )
    except ValueError as exc:  # noqa: PERF203
        detail = str(exc) or "invalid_status"
        if detail == "comment_not_found":
            raise AdminQueryError(404, "not_found") from None
        raise AdminQueryError(400, detail) from None

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
        audit_actor=actor,
        audit_resource_type="comment",
        audit_resource_id=str(updated.id),
        audit_reason=reason,
        audit_extra={"status": updated.status},
    )
    response: dict[str, Any] = {"comment": _comment_dto_to_dict(updated)}
    if comments_summary is not None:
        response["comments"] = comments_summary
    return response


async def delete_comment(
    container,
    *,
    comment_id: int,
    actor_id: str | None,
    hard: bool,
    reason: str | None,
) -> dict[str, Any]:
    actor = actor_id or SYSTEM_ACTOR_ID
    svc = container.nodes_service
    comment = await svc.get_comment(int(comment_id))
    if comment is None:
        raise AdminQueryError(404, "not_found")
    removed = await svc.delete_comment(
        int(comment_id), actor_id=actor, hard=bool(hard), reason=reason
    )
    if not removed:
        raise AdminQueryError(404, "not_found")
    await _emit_admin_activity(
        container,
        event="node.comment.deleted.admin",
        payload={
            "id": comment.id,
            "node_id": comment.node_id,
            "hard": bool(hard),
            "actor_id": actor,
        },
        key=f"node:{comment.node_id}:comment:{comment.id}:delete",
        event_context={
            "node_id": comment.node_id,
            "comment_id": comment.id,
            "source": "admin_comment_delete",
        },
        audit_action="product.nodes.comments.delete",
        audit_actor=actor,
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


async def list_nodes_admin(
    container,
    *,
    q: str | None,
    slug: str | None,
    tag: str | None,
    author_id: str | None,
    limit: int,
    offset: int,
    status: str | None,
    moderation_status: str | None,
    updated_from: str | None,
    updated_to: str | None,
    sort: str | None,
    order: str | None,
) -> list[dict[str, Any]]:
    engine = await _ensure_engine(container)
    embedding_enabled = bool(getattr(container.settings, "embedding_enabled", True))
    if engine is None:
        service = getattr(container, "nodes_service", None)
        repo = getattr(service, "repo", None) if service else None
        nodes: list[Any] = []
        if repo is not None:
            raw_nodes = getattr(repo, "_nodes", None)
            if isinstance(raw_nodes, dict):
                nodes = list(raw_nodes.values())
        if not nodes:
            return []
        store = _get_moderation_memory(container)
        status_map = store["status"]
        updated_map = store["updated_at"]
        results = []
        for dto in nodes:
            key = str(dto.id)
            results.append(
                {
                    "id": key,
                    "slug": dto.slug,
                    "title": dto.title,
                    "is_public": dto.is_public,
                    "author_id": dto.author_id,
                    "moderation_status": status_map.get(key, "pending"),
                    "moderation_status_updated_at": updated_map.get(key),
                }
            )
        return results[offset : offset + limit]

    where = ["1=1"]
    params: dict[str, Any] = {"limit": limit, "offset": offset}
    mod_filter = (
        (moderation_status or "").strip().lower() if moderation_status else None
    )
    tag_filter = (tag or "").strip().lower() if tag else None
    dev_blog_clause = "NOT EXISTS (SELECT 1 FROM product_node_tags AS dt WHERE dt.node_id = n.id AND dt.slug = :dev_tag)"
    if tag_filter:
        where.append(
            "EXISTS (SELECT 1 FROM product_node_tags AS t WHERE t.node_id = n.id AND t.slug = :tag_slug)"
        )
        params["tag_slug"] = tag_filter
        if tag_filter != DEV_BLOG_TAG:
            where.append(dev_blog_clause)
            params["dev_tag"] = DEV_BLOG_TAG
    else:
        where.append(dev_blog_clause)
        params["dev_tag"] = DEV_BLOG_TAG
    if q:
        where.append(
            "(n.title ILIKE :q OR n.slug ILIKE :q OR cast(n.id as text) = :qid)"
        )
        params["q"] = f"%{q}%"
        params["qid"] = str(q)
    if slug:
        where.append("n.slug = :slug")
        params["slug"] = str(slug)
    if author_id:
        where.append("n.author_id = cast(:author_id as uuid)")
        params["author_id"] = str(author_id)
    if updated_from:
        where.append("n.updated_at >= cast(:updated_from as timestamptz)")
        params["updated_from"] = updated_from
    if updated_to:
        where.append("n.updated_at <= cast(:updated_to as timestamptz)")
        params["updated_to"] = updated_to
    status_filter = (status or "all").lower()
    if status_filter not in {"all", "any"}:
        where.append("COALESCE(n.status, '') = :status_filter")
        params["status_filter"] = status_filter
    sort_field = (sort or "updated_at").strip().lower()
    order_clause = "DESC" if (order or "desc").lower() == "desc" else "ASC"
    valid_sort = {
        "updated_at": "n.updated_at",
        "created_at": "n.created_at",
        "views": "n.views_count",
        "comments": "stats.total_comments",
    }
    sort_column = valid_sort.get(sort_field, "n.updated_at")

    sql = f"""
        SELECT
            n.id,
            n.slug,
            n.title,
            n.author_id::text AS author_id,
            n.status,
            n.is_public,
            n.updated_at,
            n.created_at,
            n.views_count,
            n.embedding_ready,
            n.embedding_status,
            stats.total_comments,
            stats.pending_count,
            stats.published_count,
            stats.hidden_count,
            stats.deleted_count,
            stats.blocked_count,
            stats.bans_count,
            stats.last_comment_created_at,
            stats.last_comment_updated_at,
            n.moderation_status,
            n.moderation_status_updated_at
        FROM nodes AS n
        LEFT JOIN LATERAL (
            SELECT
                COUNT(*)::bigint AS total_comments,
                COALESCE(SUM(CASE WHEN status = 'pending' THEN 1 ELSE 0 END), 0)::bigint AS pending_count,
                COALESCE(SUM(CASE WHEN status = 'published' THEN 1 ELSE 0 END), 0)::bigint AS published_count,
                COALESCE(SUM(CASE WHEN status = 'hidden' THEN 1 ELSE 0 END), 0)::bigint AS hidden_count,
                COALESCE(SUM(CASE WHEN status = 'deleted' THEN 1 ELSE 0 END), 0)::bigint AS deleted_count,
                COALESCE(SUM(CASE WHEN status = 'blocked' THEN 1 ELSE 0 END), 0)::bigint AS blocked_count,
                (SELECT COUNT(*)::bigint FROM node_comment_bans b WHERE b.node_id = n.id) AS bans_count,
                MAX(created_at) AS last_comment_created_at,
                MAX(updated_at) AS last_comment_updated_at
            FROM node_comments
            WHERE node_id = n.id
        ) AS stats ON TRUE
        WHERE {' AND '.join(where)}
        ORDER BY {sort_column} {order_clause} NULLS LAST, n.id {order_clause}
        LIMIT :limit OFFSET :offset
    """

    items: list[dict[str, Any]] = []
    try:
        async with engine.begin() as conn:
            rows = (await conn.execute(text(sql), params)).mappings().all()
            items.extend(dict(row) for row in rows)
            if not items and slug and sort_column != "n.updated_at":
                params2 = dict(params)
                params2["limit"] = limit
                params2["offset"] = offset
                where2 = ["n.slug = :slug"]
                if tag_filter:
                    where2.append(
                        "EXISTS (SELECT 1 FROM product_node_tags AS t WHERE t.node_id = n.id AND t.slug = :tag_slug)"
                    )
                    if tag_filter != DEV_BLOG_TAG:
                        where2.append(dev_blog_clause)
                else:
                    where2.append(dev_blog_clause)
                if q:
                    where2.append("(COALESCE(n.title, n.slug) ILIKE :q)")
                st = (status or "all").lower()
                if st in ("published", "draft"):
                    where2.append("COALESCE(n.status, '') = :st")
                    params2["st"] = st
                sql2 = f"""
                    SELECT n.slug AS id,
                           n.slug AS slug,
                           COALESCE(n.title, n.slug) AS title,
                           n.is_public AS is_public,
                           n.updated_at,
                           n.author_id::text AS author_id,
                           COALESCE(u.username, u.email, n.author_id::text) AS author_name
                      FROM nodes AS n
                      LEFT JOIN users AS u ON u.id = n.author_id
                     WHERE {' AND '.join(where2)}
                  ORDER BY n.updated_at DESC NULLS LAST, n.slug DESC
                     LIMIT :limit OFFSET :offset
                """
                res2 = await conn.execute(text(sql2), params2)
                items.extend(dict(row) for row in res2.mappings())
    except SQLAlchemyError as exc:
        logger.debug(
            "nodes_admin_query_failed",
            extra={"query": "nodes_list", "error": str(exc)},
            exc_info=exc,
        )

    normalized: list[dict[str, Any]] = []
    for it in items:
        nid = it.get("id")
        str_id = "" if nid is None else str(nid)
        slug_val = it.get("slug")
        ready_flag = it.get("embedding_ready")
        ready = False
        if ready_flag is not None:
            ready = bool(ready_flag)
        elif embedding_enabled:
            dto = None
            candidate_id: int | None = None
            try:
                candidate_id = int(str_id) if str_id else None
            except (TypeError, ValueError):
                candidate_id = None
            service = getattr(container, "nodes_service", None)
            if service is not None:
                if candidate_id is not None:
                    dto = await service._repo_get_async(candidate_id)
                if dto is None:
                    slug_candidate = slug_val or str_id or None
                    if slug_candidate:
                        dto = await service._repo_get_by_slug_async(str(slug_candidate))
                if dto is not None and getattr(dto, "embedding", None):
                    try:
                        ready = bool(dto.embedding)
                    except TypeError:
                        ready = True
        mod_status = _normalize_moderation_status(it.get("moderation_status"))
        mod_updated = _iso(it.get("moderation_status_updated_at"))
        status_val = (
            "disabled" if not embedding_enabled else ("ready" if ready else "pending")
        )
        normalized.append(
            {
                "id": str_id,
                "slug": (
                    str(slug_val)
                    if slug_val
                    else (f"node-{str_id}" if str_id else None)
                ),
                "title": it.get("title"),
                "is_public": it.get("is_public"),
                "updated_at": it.get("updated_at"),
                "author_name": it.get("author_name") or it.get("author_id"),
                "author_id": it.get("author_id"),
                "embedding_ready": ready,
                "embedding_status": status_val,
                "moderation_status": mod_status,
                "moderation_status_updated_at": mod_updated,
            }
        )
    if mod_filter:
        normalized = [
            item
            for item in normalized
            if _normalize_moderation_status(item.get("moderation_status")) == mod_filter
        ]
    return normalized


async def get_node_engagement(
    container,
    *,
    node_identifier: str,
) -> dict[str, Any]:
    engine = await _ensure_engine(container)
    if engine is not None:
        try:
            resolved_id = await _resolve_node_id(node_identifier, container, engine)
            return await _fetch_engagement_summary(engine, resolved_id)
        except Exception as exc:  # noqa: BLE001
            logger.debug(
                "nodes_admin_engagement_fallback",
                extra={"node_identifier": node_identifier},
                exc_info=exc,
            )
            engine = None
    dto = await _resolve_memory_node(container, node_identifier)
    if dto is None:
        raise AdminQueryError(404, "not_found")
    service = getattr(container, "nodes_service", None)
    if service is None:
        raise AdminQueryError(500, "service_unavailable")
    total_views = await service.get_total_views(int(dto.id))
    return {"id": str(dto.id), "views_count": int(total_views or 0)}


async def delete_node(
    container,
    *,
    node_id: int,
    actor_id: str | None,
) -> dict[str, Any]:
    service = getattr(container, "nodes_service", None)
    if service is None:
        raise AdminQueryError(500, "service_unavailable")
    try:
        ok = await service.delete(node_id)
    except AdminQueryError:
        raise
    except (SQLAlchemyError, RuntimeError, ValueError) as exc:
        logger.error(
            "nodes_admin_delete_failed", extra={"node_id": node_id}, exc_info=exc
        )
        raise AdminQueryError(500, "delete_failed") from exc
    if not ok:
        raise AdminQueryError(404, "not_found")
    await _emit_admin_activity(
        container,
        audit_action="product.nodes.delete",
        audit_actor=actor_id or SYSTEM_ACTOR_ID,
        audit_resource_type="node",
        audit_resource_id=str(node_id),
        audit_extra={"source": "admin_delete"},
    )
    return {"ok": True}


async def bulk_update_status(
    container,
    *,
    ids: Iterable[int],
    status: str,
    publish_at: str | None,
    unpublish_at: str | None,
    actor_id: str | None,
) -> dict[str, Any]:
    ids = list(ids)
    if not ids:
        raise AdminQueryError(400, "ids_required")
    if not status:
        raise AdminQueryError(400, "status_required")
    engine = await _ensure_engine(container)
    if engine is None:
        raise AdminQueryError(500, "no_engine")
    is_pub = status in ("published", "scheduled_unpublish")
    try:
        async with engine.begin() as conn:
            sql = text(
                """
                UPDATE nodes AS n
                   SET status = :status,
                       is_public = :pub,
                       publish_at = COALESCE(cast(:publish_at as timestamptz), publish_at),
                       unpublish_at = COALESCE(cast(:unpublish_at as timestamptz), unpublish_at),
                       updated_at = now()
                 WHERE n.id = ANY(:ids)
                """
            )
            await conn.execute(
                sql,
                {
                    "status": status,
                    "pub": bool(is_pub),
                    "publish_at": publish_at,
                    "unpublish_at": unpublish_at,
                    "ids": ids,
                },
            )
    except SQLAlchemyError as exc:
        logger.error(
            "nodes_admin_bulk_status_failed",
            extra={"ids": ids},
            exc_info=exc,
        )
        raise AdminQueryError(500, "bulk_status_failed") from exc
    for nid in ids:
        await _emit_admin_activity(
            container,
            event="node.updated.v1",
            payload={
                "id": int(nid),
                "fields": ["status", "publish_at", "unpublish_at"],
            },
            key=f"node:{int(nid)}",
            event_context={"node_id": int(nid), "source": "bulk_status"},
        )
    await _emit_admin_activity(
        container,
        audit_action="product.nodes.bulk_status",
        audit_actor=actor_id or SYSTEM_ACTOR_ID,
        audit_resource_type="node",
        audit_resource_id=None,
        audit_extra={
            "ids": ids,
            "status": status,
            "publish_at": publish_at,
            "unpublish_at": unpublish_at,
            "count": len(ids),
        },
    )
    return {"ok": True}


async def bulk_update_tags(
    container,
    *,
    ids: Iterable[int],
    tags: Iterable[str],
    action: str,
    actor_id: str | None,
) -> dict[str, Any]:
    ids = [int(i) for i in ids]
    if not ids:
        raise AdminQueryError(400, "ids_required")
    slugs = [str(s).strip().lower() for s in tags if str(s).strip()]
    if not slugs:
        return {"ok": True, "updated": 0}
    action_norm = (action or "").lower()
    if action_norm not in {"add", "remove"}:
        raise AdminQueryError(400, "action_invalid")
    engine = await _ensure_engine(container)
    if engine is None:
        raise AdminQueryError(500, "no_engine")
    updated = 0
    try:
        async with engine.begin() as conn:
            if action_norm == "add":
                for nid in ids:
                    for slug in slugs:
                        await conn.execute(
                            text(
                                "INSERT INTO product_node_tags(node_id, slug) VALUES (:id, :slug) ON CONFLICT DO NOTHING"
                            ),
                            {"id": nid, "slug": slug},
                        )
                        updated += 1
            else:
                await conn.execute(
                    text(
                        "DELETE FROM product_node_tags WHERE node_id = ANY(:ids) AND slug = ANY(:slugs)"
                    ),
                    {"ids": ids, "slugs": slugs},
                )
    except SQLAlchemyError as exc:
        logger.error(
            "nodes_admin_bulk_tags_failed",
            extra={"ids": ids, "action": action_norm},
            exc_info=exc,
        )
        raise AdminQueryError(500, "bulk_tags_failed") from exc
    for nid in ids:
        await _emit_admin_activity(
            container,
            event="node.tags.updated.v1",
            payload={"id": nid, "tags": slugs, "action": action_norm},
            key=f"node:{nid}:tags",
            event_context={
                "node_id": nid,
                "source": "bulk_tags",
                "action": action_norm,
            },
        )
    await _emit_admin_activity(
        container,
        audit_action="product.nodes.bulk_tags",
        audit_actor=actor_id or SYSTEM_ACTOR_ID,
        audit_resource_type="node",
        audit_resource_id=None,
        audit_extra={
            "ids": ids,
            "action": action_norm,
            "tags": slugs,
            "updated": updated,
        },
    )
    return {"ok": True, "updated": updated}


async def restore_node(
    container,
    *,
    node_id: int,
    actor_id: str | None,
) -> dict[str, Any]:
    engine = await _ensure_engine(container)
    if engine is None:
        raise AdminQueryError(500, "no_engine")
    try:
        async with engine.begin() as conn:
            res = await conn.execute(
                text(
                    "UPDATE nodes SET status = 'draft', is_public = false, publish_at = NULL, unpublish_at = NULL, updated_at = now() WHERE id = :id AND status = 'deleted'"
                ),
                {"id": int(node_id)},
            )
            rowcount = res.rowcount if hasattr(res, "rowcount") else None
    except SQLAlchemyError as exc:
        logger.error(
            "nodes_admin_restore_failed", extra={"node_id": node_id}, exc_info=exc
        )
        raise AdminQueryError(500, "restore_failed") from exc
    if not rowcount:
        raise AdminQueryError(404, "not_found")
    await _emit_admin_activity(
        container,
        event="node.updated.v1",
        payload={
            "id": int(node_id),
            "fields": ["status", "publish_at", "unpublish_at", "is_public"],
        },
        key=f"node:{int(node_id)}",
        event_context={"node_id": int(node_id), "source": "restore_node"},
    )
    await _emit_admin_activity(
        container,
        audit_action="product.nodes.restore",
        audit_actor=actor_id or SYSTEM_ACTOR_ID,
        audit_resource_type="node",
        audit_resource_id=str(node_id),
        audit_extra={"source": "restore_node"},
    )
    return {"ok": True}


__all__ = [
    "apply_moderation_decision",
    "build_analytics_csv",
    "bulk_update_status",
    "bulk_update_tags",
    "create_comment_ban",
    "delete_comment",
    "delete_comment_ban",
    "delete_node",
    "fetch_node_analytics",
    "get_moderation_detail",
    "get_node_engagement",
    "list_comment_bans",
    "list_node_comments",
    "list_nodes_admin",
    "restore_node",
    "set_comments_disabled",
    "set_comments_lock",
    "update_comment_status",
    "logger",
]

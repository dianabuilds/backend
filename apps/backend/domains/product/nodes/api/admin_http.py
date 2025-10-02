from __future__ import annotations

import json
from datetime import UTC, datetime
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Query, Request
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncEngine

from apps.backend import get_container
from domains.platform.iam.security import csrf_protect, get_current_user, require_admin
from packages.core.config import to_async_dsn
from packages.core.db import get_async_engine


async def _ensure_engine(container) -> AsyncEngine | None:
    try:
        dsn = to_async_dsn(container.settings.database_url)
        # Hard-strip query to avoid any lingering client-unsupported params
        if "?" in dsn:
            dsn = dsn.split("?", 1)[0]
        if not dsn:
            return None
        return get_async_engine("nodes-admin", url=dsn, future=True)
    except Exception:
        return None


def _iso(value: Any) -> str | None:
    if value is None:
        return None
    if isinstance(value, datetime):
        if value.tzinfo is None:
            value = value.replace(tzinfo=UTC)
        return value.astimezone(UTC).isoformat().replace("+00:00", "Z")
    try:
        parsed = datetime.fromisoformat(str(value))
    except Exception:
        return None
    return _iso(parsed)


_ALLOWED_MODERATION_STATUSES = {
    "pending",
    "resolved",
    "hidden",
    "restricted",
    "escalated",
}
_DECISION_STATUS_MAP = {
    "keep": "resolved",
    "hide": "hidden",
    "delete": "hidden",
    "restrict": "restricted",
    "escalate": "escalated",
    "review": "pending",
}


def _normalize_moderation_status(value: Any) -> str:
    try:
        result = str(value or "").strip().lower()
    except Exception:
        result = ""
    if result not in _ALLOWED_MODERATION_STATUSES:
        return "pending"
    return result


def _decision_to_status(action: str) -> str:
    return _DECISION_STATUS_MAP.get(action, "pending")


def _extract_actor_id(request: Request) -> str | None:
    try:
        ctx = getattr(request.state, "auth_context", None)
    except Exception:
        ctx = None
    if isinstance(ctx, dict):
        candidate = ctx.get("actor_id") or ctx.get("user_id") or ctx.get("sub")
        if candidate:
            return str(candidate)
    header_actor = request.headers.get("X-Actor-Id") or request.headers.get("x-actor-id")
    if header_actor:
        candidate = header_actor.strip()
        if candidate:
            return candidate
    return None


async def _resolve_node_id(node_identifier: str, container, engine: AsyncEngine) -> int:
    try:
        return int(str(node_identifier))
    except Exception:
        pass
    candidate = str(node_identifier)
    try:
        dto = await container.nodes_service._repo_get_by_slug_async(candidate)
    except Exception:
        dto = None
    if dto is not None and getattr(dto, "id", None) is not None:
        try:
            return int(dto.id)  # type: ignore[arg-type]
        except Exception:
            pass
    async with engine.begin() as conn:
        resolved = (
            await conn.execute(
                text("SELECT id FROM nodes WHERE slug = :slug"),
                {"slug": candidate},
            )
        ).scalar()
    if resolved is None:
        raise HTTPException(status_code=404, detail="not_found")
    return int(resolved)


async def _fetch_moderation_detail(engine: AsyncEngine, node_id: int) -> dict[str, Any] | None:
    async with engine.begin() as conn:
        row = (
            (
                await conn.execute(
                    text(
                        """
                    SELECT id,
                           slug,
                           title,
                           author_id::text AS author_id,
                           status,
                           is_public,
                           created_at,
                           updated_at,
                           moderation_status,
                           moderation_status_updated_at
                    FROM nodes
                    WHERE id = :id
                    """
                    ),
                    {"id": node_id},
                )
            )
            .mappings()
            .first()
        )
        if row is None:
            return None
        history_rows = (
            (
                await conn.execute(
                    text(
                        """
                    SELECT id,
                           action,
                           status,
                           reason,
                           actor_id,
                           decided_at
                    FROM node_moderation_history
                    WHERE node_id = :id
                    ORDER BY decided_at DESC
                    LIMIT 100
                    """
                    ),
                    {"id": node_id},
                )
            )
            .mappings()
            .all()
        )
    return _build_moderation_detail(row, history_rows)


def _build_moderation_detail(
    row: dict[str, Any], history_rows: list[dict[str, Any]]
) -> dict[str, Any]:
    moderation_status = _normalize_moderation_status(row.get("moderation_status"))
    history: list[dict[str, Any]] = []
    for entry in history_rows:
        history.append(
            {
                "action": entry.get("action"),
                "status": _normalize_moderation_status(entry.get("status")),
                "reason": entry.get("reason"),
                "actor": entry.get("actor_id"),
                "decided_at": _iso(entry.get("decided_at")),
            }
        )
    meta: dict[str, Any] = {
        "node_status": row.get("status"),
        "moderation_status": moderation_status,
        "moderation_status_updated_at": _iso(row.get("moderation_status_updated_at")),
        "created_at": _iso(row.get("created_at")),
        "updated_at": _iso(row.get("updated_at")),
        "slug": row.get("slug"),
        "is_public": row.get("is_public"),
    }
    return {
        "id": str(row.get("id")),
        "type": "node",
        "author_id": row.get("author_id"),
        "preview": row.get("title"),
        "status": moderation_status,
        "moderation_history": history,
        "meta": meta,
        "reports": [],
    }


def make_router() -> APIRouter:
    router = APIRouter(prefix="/v1/admin/nodes", tags=["admin-nodes"])

    @router.get("/list", summary="List nodes for admin")
    async def list_nodes(
        q: str | None = Query(default=None),
        slug: str | None = Query(default=None, description="Filter by exact slug"),
        author_id: str | None = Query(default=None, description="Filter by author id (UUID)"),
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
        eng = await _ensure_engine(container)
        embedding_enabled = bool(getattr(container.settings, "embedding_enabled", True))
        if eng is None:
            # Fallback to service by author if engine is not configured
            # This path is mainly for local/no-db runs
            try:
                rows = container.nodes_service.list_by_author(
                    getattr(container, "current_user_id", "") or "",
                    limit=limit,
                    offset=offset,
                )
                return [
                    {
                        "id": str(r.id),
                        "slug": f"node-{r.id}",
                        "title": r.title,
                        "is_public": r.is_public,
                        "author_name": None,
                        "updated_at": None,
                    }
                    for r in rows
                ]
            except Exception:
                return []

        where = ["1=1"]
        params: dict[str, Any] = {"limit": limit, "offset": offset}
        mod_filter = (moderation_status or "").strip().lower() if moderation_status else None
        if q:
            where.append("(n.title ILIKE :q OR n.slug ILIKE :q OR cast(n.id as text) = :qid)")
            params["q"] = f"%{q}%"
            params["qid"] = str(q)
        if slug:
            where.append("n.slug = :slug")
            params["slug"] = str(slug)
        if author_id:
            where.append("n.author_id = cast(:aid as uuid)")
            params["aid"] = str(author_id)
        st = (status or "all").lower()
        # Prefer new status column; fallback to is_public where needed
        # We will render two different base SQLs accordingly
        # Date filters
        if updated_from:
            where.append("n.updated_at >= cast(:updated_from as timestamptz)")
            params["updated_from"] = str(updated_from)
        if updated_to:
            where.append("n.updated_at <= cast(:updated_to as timestamptz)")
            params["updated_to"] = str(updated_to)

        def base_sql(
            table: str,
            include_slug: bool,
            include_status: bool,
            include_embedding: bool,
            include_moderation: bool,
        ) -> str:
            slug_expr = "n.slug AS slug," if include_slug else "NULL::text AS slug,"
            status_expr = "n.status AS status," if include_status else "NULL::text AS status,"
            embedding_expr = (
                "(n.embedding IS NOT NULL) AS embedding_ready,"
                if include_embedding
                else "NULL::bool AS embedding_ready,"
            )
            moderation_expr = (
                "n.moderation_status AS moderation_status,"
                if include_moderation
                else "NULL::text AS moderation_status,"
            )
            moderation_ts_expr = (
                "n.moderation_status_updated_at AS moderation_status_updated_at,"
                if include_moderation
                else "NULL::timestamptz AS moderation_status_updated_at,"
            )
            where_local = list(where)
            if include_status and st in (
                "published",
                "draft",
                "scheduled",
                "scheduled_unpublish",
                "archived",
                "deleted",
            ):
                where_local.append("n.status = :st")
                params["st"] = st
            elif st in ("published", "draft"):
                where_local.append("n.is_public = :pub")
                params["pub"] = True if st == "published" else False
            if include_moderation and mod_filter:
                where_local.append("COALESCE(n.moderation_status, 'pending') = :mod_filter")
                params["mod_filter"] = mod_filter
            # Sorting (whitelist)
            s = (sort or "updated_at").lower()
            o = (order or "desc").lower()
            s_map = {
                "updated_at": "n.updated_at",
                "title": "n.title",
                "author": "author_name",
                "status": "n.status",
            }
            col = s_map.get(s, "n.updated_at")
            dir_sql = "ASC" if o == "asc" else "DESC"
            order_by = f"{col} {dir_sql}, n.id DESC"
            return f"""
              SELECT n.id,
                     n.title,
                     n.is_public,
                     {status_expr}
                     {moderation_expr}
                     {moderation_ts_expr}
                     n.updated_at,
                     {slug_expr}
                     n.author_id::text AS author_id,
                     {embedding_expr}
                     COALESCE(u.username, u.email, n.author_id::text) AS author_name
              FROM {table} AS n
              LEFT JOIN users AS u ON u.id = n.author_id
              WHERE {' AND '.join(where_local)}
              ORDER BY {order_by}
              LIMIT :limit OFFSET :offset
            """

        async with eng.begin() as conn:
            has_slug_column = False
            try:
                chk = await conn.execute(
                    text(
                        "SELECT 1 FROM information_schema.columns WHERE table_schema = 'public' AND table_name = 'nodes' AND column_name = 'slug'"
                    )
                )
                has_slug_column = bool(chk.scalar())
            except Exception:
                has_slug_column = False
            try:
                chk2 = await conn.execute(
                    text(
                        "SELECT 1 FROM information_schema.columns WHERE table_schema = 'public' AND table_name = 'nodes' AND column_name = 'status'"
                    )
                )
                has_status_column = bool(chk2.scalar())
            except Exception:
                has_status_column = False
            try:
                chk3 = await conn.execute(
                    text(
                        "SELECT 1 FROM information_schema.columns WHERE table_schema = 'public' AND table_name = 'nodes' AND column_name = 'embedding'"
                    )
                )
                has_embedding_column = bool(chk3.scalar())
            except Exception:
                has_embedding_column = False
            try:
                chk4 = await conn.execute(
                    text(
                        "SELECT 1 FROM information_schema.columns WHERE table_schema = 'public' AND table_name = 'nodes' AND column_name = 'moderation_status'"
                    )
                )
                has_moderation_column = bool(chk4.scalar())
            except Exception:
                has_moderation_column = False

            items: list[dict[str, Any]] = []
            try:
                res = await conn.execute(
                    text(
                        base_sql(
                            "nodes",
                            has_slug_column,
                            has_status_column,
                            has_embedding_column,
                            has_moderation_column,
                        )
                    ),
                    params,
                )
                for row in res.mappings():
                    items.append(
                        {
                            "id": row["id"],
                            "title": row["title"],
                            "is_public": bool(row["is_public"]),
                            "status": row.get("status"),
                            "updated_at": row.get("updated_at"),
                            "author_name": row.get("author_name"),
                            "author_id": row.get("author_id"),
                            "slug": row.get("slug"),
                            "embedding_ready": row.get("embedding_ready"),
                            "moderation_status": row.get("moderation_status"),
                            "moderation_status_updated_at": row.get("moderation_status_updated_at"),
                        }
                    )
            except Exception:
                items = []
            if not items:
                try:
                    where2 = ["1=1"]
                    params2 = dict(params)
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
                    for row in res2.mappings():
                        items.append(
                            {
                                "id": row.get("id"),
                                "title": row.get("title"),
                                "is_public": bool(row.get("is_public", False)),
                                "updated_at": row.get("updated_at"),
                                "author_name": row.get("author_name"),
                                "author_id": row.get("author_id"),
                                "slug": row.get("slug") or row.get("id"),
                                "embedding_ready": None,
                                "moderation_status": None,
                                "moderation_status_updated_at": None,
                            }
                        )
                except Exception:
                    pass

        normalized: list[dict[str, Any]] = []
        for it in items:
            nid = it.get("id")
            try:
                str_id = str(nid)
            except Exception:
                str_id = ""
            slug = it.get("slug")
            ready_flag = it.get("embedding_ready")
            ready = False
            if ready_flag is not None:
                if isinstance(ready_flag, bool):
                    ready = ready_flag
                else:
                    ready = str(ready_flag).lower() in {"true", "t", "1"}
            elif embedding_enabled:
                dto = None
                candidate_id: int | None = None
                try:
                    candidate_id = int(str_id) if str_id else None
                except Exception:
                    candidate_id = None
                if candidate_id is not None:
                    dto = await container.nodes_service._repo_get_async(candidate_id)
                if dto is None:
                    slug_candidate = slug or str_id or None
                    if slug_candidate:
                        dto = await container.nodes_service._repo_get_by_slug_async(
                            str(slug_candidate)
                        )
                if dto is not None and dto.embedding:
                    try:
                        ready = len(dto.embedding) > 0
                    except Exception:
                        ready = True
            mod_status = _normalize_moderation_status(it.get("moderation_status"))
            mod_updated = _iso(it.get("moderation_status_updated_at"))
            status_val = "disabled" if not embedding_enabled else ("ready" if ready else "pending")
            normalized.append(
                {
                    "id": str_id,
                    "slug": (str(slug) if slug else (f"node-{str_id}" if str_id else None)),
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
                actor_id = str(claims.get("sub") or "") or None
            except Exception:
                actor_id = None
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
        payload_json = json.dumps(payload_extra, default=str)
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
        detail = await _fetch_moderation_detail(eng, node_pk)
        event_payload = {
            "id": node_pk,
            "action": action,
            "status": moderation_status,
            "reason": reason,
            "actor_id": actor_id,
            "decided_at": _iso(decided_at),
        }
        try:
            container.events.publish(
                "node.moderation.decision.v1",
                event_payload,
                key=f"node:{node_pk}:moderation",
            )
        except Exception:
            pass
        try:
            container.events.publish(
                "node.updated.v1",
                {"id": node_pk, "fields": node_update_fields},
                key=f"node:{node_pk}",
            )
        except Exception:
            pass
        return detail or {"ok": True, "status": moderation_status}

    @router.delete("/{node_id}", summary="Admin delete node")
    async def admin_delete(
        node_id: int,
        _csrf: None = Depends(csrf_protect),
        _: None = Depends(require_admin),
        container=Depends(get_container),
    ):
        try:
            ok = await container.nodes_service.delete(node_id)
            if not ok:
                raise HTTPException(status_code=404, detail="not_found")
            return {"ok": True}
        except HTTPException:
            raise
        except Exception:
            raise HTTPException(status_code=500, detail="delete_failed") from None

    @router.post("/bulk/status", summary="Bulk update node status")
    async def bulk_status(
        body: dict,
        _csrf: None = Depends(csrf_protect),
        _: None = Depends(require_admin),
        container=Depends(get_container),
    ):
        ids = body.get("ids") or []
        status = body.get("status")
        publish_at = body.get("publish_at")
        unpublish_at = body.get("unpublish_at")
        if not isinstance(ids, list) or not ids:
            raise HTTPException(status_code=400, detail="ids_required")
        if not isinstance(status, str) or not status:
            raise HTTPException(status_code=400, detail="status_required")
        eng = await _ensure_engine(container)
        if eng is None:
            raise HTTPException(status_code=500, detail="no_engine")
        # derive is_public flag from target status
        is_pub = True if status in ("published", "scheduled_unpublish") else False
        async with eng.begin() as conn:
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
                    "ids": [int(i) for i in ids],
                },
            )
        try:
            for nid in ids:
                container.events.publish(
                    "node.updated.v1",
                    {
                        "id": int(nid),
                        "fields": ["status", "publish_at", "unpublish_at"],
                    },
                    key=f"node:{int(nid)}",
                )
        except Exception:
            pass
        return {"ok": True}

    @router.post("/bulk/tags", summary="Bulk add/remove tags")
    async def bulk_tags(
        body: dict,
        _csrf: None = Depends(csrf_protect),
        _: None = Depends(require_admin),
        container=Depends(get_container),
    ):
        ids = body.get("ids") or []
        tags = body.get("tags") or []
        action = str(body.get("action") or "").lower()
        if not isinstance(ids, list) or not ids:
            raise HTTPException(status_code=400, detail="ids_required")
        if not isinstance(tags, list) or not tags:
            raise HTTPException(status_code=400, detail="tags_required")
        if action not in ("add", "remove"):
            raise HTTPException(status_code=400, detail="action_invalid")
        slugs = [str(s).strip().lower() for s in tags if str(s).strip()]
        if not slugs:
            return {"ok": True, "updated": 0}
        eng = await _ensure_engine(container)
        if eng is None:
            raise HTTPException(status_code=500, detail="no_engine")
        updated = 0
        async with eng.begin() as conn:
            if action == "add":
                for nid in ids:
                    for s in slugs:
                        await conn.execute(
                            text(
                                "INSERT INTO product_node_tags(node_id, slug) VALUES (:id, :slug) ON CONFLICT DO NOTHING"
                            ),
                            {"id": int(nid), "slug": s},
                        )
                        updated += 1
            else:
                await conn.execute(
                    text(
                        "DELETE FROM product_node_tags WHERE node_id = ANY(:ids) AND slug = ANY(:slugs)"
                    ),
                    {"ids": [int(i) for i in ids], "slugs": slugs},
                )
        try:
            for nid in ids:
                container.events.publish(
                    "node.tags.updated.v1",
                    {"id": int(nid), "tags": slugs, "action": action},
                    key=f"node:{int(nid)}:tags",
                )
        except Exception:
            pass
        return {"ok": True, "updated": updated}

    @router.post("/{node_id}/restore", summary="Restore soft-deleted node")
    async def restore_node(
        node_id: int,
        _csrf: None = Depends(csrf_protect),
        _: None = Depends(require_admin),
        container=Depends(get_container),
    ):
        eng = await _ensure_engine(container)
        if eng is None:
            raise HTTPException(status_code=500, detail="no_engine")
        async with eng.begin() as conn:
            res = await conn.execute(
                text(
                    "UPDATE nodes SET status = 'draft', is_public = false, publish_at = NULL, unpublish_at = NULL, updated_at = now() WHERE id = :id AND status = 'deleted'"
                ),
                {"id": int(node_id)},
            )
            try:
                rc = res.rowcount  # type: ignore[attr-defined]
            except Exception:
                rc = None
        if not rc:
            raise HTTPException(status_code=404, detail="not_found")
        try:
            container.events.publish(
                "node.updated.v1",
                {
                    "id": int(node_id),
                    "fields": ["status", "publish_at", "unpublish_at", "is_public"],
                },
                key=f"node:{int(node_id)}",
            )
        except Exception:
            pass
        return {"ok": True}

    return router

from __future__ import annotations

from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Query, Request
from sqlalchemy import text
from sqlalchemy.exc import SQLAlchemyError

from apps.backend import get_container
from domains.platform.iam.security import (  # type: ignore[import-not-found]
    csrf_protect,
    require_admin,
)

from .admin_common import (
    SYSTEM_ACTOR_ID,
    _emit_admin_activity,
    _ensure_engine,
    _extract_actor_id,
    _fetch_engagement_summary,
    _iso,
    _normalize_moderation_status,
    _resolve_node_id,
    logger,
)


def register_nodes_routes(router: APIRouter) -> None:
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
            except (AttributeError, RuntimeError, SQLAlchemyError) as exc:
                logger.warning(
                    "nodes_admin_fallback_list_failed",
                    extra={"author_id": getattr(container, "current_user_id", None)},
                    exc_info=exc,
                )
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
            except SQLAlchemyError as exc:
                logger.debug(
                    "nodes_admin_schema_check_failed",
                    extra={"column": "slug"},
                    exc_info=exc,
                )
                has_slug_column = False
            try:
                chk2 = await conn.execute(
                    text(
                        "SELECT 1 FROM information_schema.columns WHERE table_schema = 'public' AND table_name = 'nodes' AND column_name = 'status'"
                    )
                )
                has_status_column = bool(chk2.scalar())
            except SQLAlchemyError as exc:
                logger.debug(
                    "nodes_admin_schema_check_failed",
                    extra={"column": "status"},
                    exc_info=exc,
                )
                has_status_column = False
            try:
                chk3 = await conn.execute(
                    text(
                        "SELECT 1 FROM information_schema.columns WHERE table_schema = 'public' AND table_name = 'nodes' AND column_name = 'embedding'"
                    )
                )
                has_embedding_column = bool(chk3.scalar())
            except SQLAlchemyError as exc:
                logger.debug(
                    "nodes_admin_schema_check_failed",
                    extra={"column": "embedding"},
                    exc_info=exc,
                )
                has_embedding_column = False
            try:
                chk4 = await conn.execute(
                    text(
                        "SELECT 1 FROM information_schema.columns WHERE table_schema = 'public' AND table_name = 'nodes' AND column_name = 'moderation_status'"
                    )
                )
                has_moderation_column = bool(chk4.scalar())
            except SQLAlchemyError as exc:
                logger.debug(
                    "nodes_admin_schema_check_failed",
                    extra={"column": "moderation_status"},
                    exc_info=exc,
                )
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
            except SQLAlchemyError as exc:
                logger.error(
                    "nodes_admin_query_failed",
                    extra={"query": "nodes_base"},
                    exc_info=exc,
                )
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
                except SQLAlchemyError as exc:
                    logger.debug(
                        "nodes_admin_query_failed",
                        extra={"query": "nodes_fallback"},
                        exc_info=exc,
                    )

        normalized: list[dict[str, Any]] = []
        for it in items:
            nid = it.get("id")
            str_id = "" if nid is None else str(nid)
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
                except (TypeError, ValueError):
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
                    except TypeError:
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

    @router.get("/{node_id}/engagement", summary="Get node engagement summary")
    async def get_node_engagement(
        node_id: str,
        _: None = Depends(require_admin),
        container=Depends(get_container),
    ) -> dict[str, Any]:
        engine = await _ensure_engine(container)
        if engine is None:
            raise HTTPException(status_code=503, detail="database_unavailable")
        resolved_id = await _resolve_node_id(node_id, container, engine)
        return await _fetch_engagement_summary(engine, resolved_id)

    @router.delete("/{node_id}", summary="Admin delete node")
    async def admin_delete(
        node_id: int,
        request: Request,
        _csrf: None = Depends(csrf_protect),
        _: None = Depends(require_admin),
        container=Depends(get_container),
    ):
        actor_id = _extract_actor_id(request)
        try:
            ok = await container.nodes_service.delete(node_id)
        except HTTPException:
            raise
        except (SQLAlchemyError, RuntimeError, ValueError) as exc:
            logger.error("nodes_admin_delete_failed", extra={"node_id": node_id}, exc_info=exc)
            raise HTTPException(status_code=500, detail="delete_failed") from None
        if not ok:
            raise HTTPException(status_code=404, detail="not_found")
        await _emit_admin_activity(
            container,
            audit_action="product.nodes.delete",
            audit_actor=actor_id or SYSTEM_ACTOR_ID,
            audit_resource_type="node",
            audit_resource_id=str(node_id),
            audit_extra={"source": "admin_delete"},
        )
        return {"ok": True}

    @router.post("/bulk/status", summary="Bulk update node status")
    async def bulk_status(
        body: dict,
        request: Request,
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
        try:
            normalized_ids = [int(i) for i in ids]
        except (TypeError, ValueError):
            raise HTTPException(status_code=400, detail="ids_invalid") from None
        eng = await _ensure_engine(container)
        if eng is None:
            raise HTTPException(status_code=500, detail="no_engine")
        is_pub = status in ("published", "scheduled_unpublish")
        try:
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
                        "ids": normalized_ids,
                    },
                )
        except SQLAlchemyError as exc:
            logger.error(
                "nodes_admin_bulk_status_failed",
                extra={"ids": normalized_ids},
                exc_info=exc,
            )
            raise HTTPException(status_code=500, detail="bulk_status_failed") from None
        actor_id = _extract_actor_id(request)
        for nid in normalized_ids:
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
                "ids": normalized_ids,
                "status": status,
                "publish_at": publish_at,
                "unpublish_at": unpublish_at,
                "count": len(normalized_ids),
            },
        )
        return {"ok": True}

    @router.post("/bulk/tags", summary="Bulk add/remove tags")
    async def bulk_tags(
        body: dict,
        request: Request,
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
        try:
            normalized_ids = [int(i) for i in ids]
        except (TypeError, ValueError):
            raise HTTPException(status_code=400, detail="ids_invalid") from None
        eng = await _ensure_engine(container)
        if eng is None:
            raise HTTPException(status_code=500, detail="no_engine")
        updated = 0
        try:
            async with eng.begin() as conn:
                if action == "add":
                    for nid in normalized_ids:
                        for slug_value in slugs:
                            await conn.execute(
                                text(
                                    "INSERT INTO product_node_tags(node_id, slug) VALUES (:id, :slug) ON CONFLICT DO NOTHING"
                                ),
                                {"id": nid, "slug": slug_value},
                            )
                            updated += 1
                else:
                    await conn.execute(
                        text(
                            "DELETE FROM product_node_tags WHERE node_id = ANY(:ids) AND slug = ANY(:slugs)"
                        ),
                        {"ids": normalized_ids, "slugs": slugs},
                    )
        except SQLAlchemyError as exc:
            logger.error(
                "nodes_admin_bulk_tags_failed",
                extra={"ids": normalized_ids, "action": action},
                exc_info=exc,
            )
            raise HTTPException(status_code=500, detail="bulk_tags_failed") from None
        actor_id = _extract_actor_id(request)
        for nid in normalized_ids:
            await _emit_admin_activity(
                container,
                event="node.tags.updated.v1",
                payload={"id": nid, "tags": slugs, "action": action},
                key=f"node:{nid}:tags",
                event_context={"node_id": nid, "source": "bulk_tags", "action": action},
            )
        await _emit_admin_activity(
            container,
            audit_action="product.nodes.bulk_tags",
            audit_actor=actor_id or SYSTEM_ACTOR_ID,
            audit_resource_type="node",
            audit_resource_id=None,
            audit_extra={
                "ids": normalized_ids,
                "action": action,
                "tags": slugs,
                "updated": updated,
            },
        )
        return {"ok": True, "updated": updated}

    @router.post("/{node_id}/restore", summary="Restore soft-deleted node")
    async def restore_node(
        node_id: int,
        request: Request,
        _csrf: None = Depends(csrf_protect),
        _: None = Depends(require_admin),
        container=Depends(get_container),
    ):
        eng = await _ensure_engine(container)
        if eng is None:
            raise HTTPException(status_code=500, detail="no_engine")
        try:
            async with eng.begin() as conn:
                res = await conn.execute(
                    text(
                        "UPDATE nodes SET status = 'draft', is_public = false, publish_at = NULL, unpublish_at = NULL, updated_at = now() WHERE id = :id AND status = 'deleted'"
                    ),
                    {"id": int(node_id)},
                )
                rc = getattr(res, "rowcount", None)
                if callable(rc):
                    rc = rc()
        except SQLAlchemyError as exc:
            logger.error("nodes_admin_restore_failed", extra={"node_id": node_id}, exc_info=exc)
            raise HTTPException(status_code=500, detail="restore_failed") from None
        if not rc:
            raise HTTPException(status_code=404, detail="not_found")
        actor_id = _extract_actor_id(request)
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

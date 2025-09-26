from __future__ import annotations

from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncEngine

from apps.backend import get_container
from domains.platform.iam.security import csrf_protect, require_admin
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
        return get_async_engine("nodes-admin", url=dsn, cache=False, future=True)
    except Exception:
        return None


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

        def base_sql(table: str, include_slug: bool, include_status: bool) -> str:
            slug_expr = "n.slug AS slug," if include_slug else "NULL::text AS slug,"
            status_expr = "n.status AS status," if include_status else "NULL::text AS status,"
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
                     n.updated_at,
                     {slug_expr}
                     n.author_id::text AS author_id,
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

            items: list[dict[str, Any]] = []
            try:
                res = await conn.execute(
                    text(
                        base_sql(
                            "nodes",
                            has_slug_column,
                            has_status_column,
                            has_embedding_column,
                            has_embedding_column,
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
                }
            )
        return normalized

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

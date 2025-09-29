from __future__ import annotations

import uuid as _uuid

from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncEngine

from apps.backend import get_container
from domains.platform.iam.security import csrf_protect, get_current_user
from packages.core.config import to_async_dsn
from packages.core.db import get_async_engine


def make_router() -> APIRouter:
    router = APIRouter(prefix="/v1/nodes")

    async def _ensure_engine(container) -> AsyncEngine | None:
        try:
            dsn = to_async_dsn(container.settings.database_url)
            if not dsn:
                return None
            # Strip query params to avoid client unsupported params
            if "?" in dsn:
                dsn = dsn.split("?", 1)[0]
            return get_async_engine("nodes-api", url=dsn, future=True)
        except Exception:
            return None

    async def _resolve_node_ref(node_ref: str, svc):
        view = None
        resolved_id: int | None = None
        maybe_id: int | None = None
        try:
            maybe_id = int(node_ref)
        except Exception:
            maybe_id = None
        if maybe_id is not None:
            dto = await svc._repo_get_async(maybe_id)
            if dto is not None:
                resolved_id = int(dto.id)
                view = svc._to_view(dto)
        if view is None:
            dto = await svc._repo_get_by_slug_async(str(node_ref))
            if dto is not None:
                try:
                    resolved_id = int(dto.id)
                except Exception:
                    resolved_id = None
                view = svc._to_view(dto)
        return view, resolved_id

    @router.get("/{node_id}")
    async def get_node(
        node_id: str,
        req: Request,
        container=Depends(get_container),
        claims=Depends(get_current_user),
    ):
        svc = container.nodes_service
        view, _resolved_id = await _resolve_node_ref(node_id, svc)
        if not view:
            raise HTTPException(status_code=404, detail="not_found")
        if str(view.status or "").lower() == "deleted":
            raise HTTPException(status_code=404, detail="not_found")
        uid = str(claims.get("sub")) if claims else None
        role = str(claims.get("role") or "").lower()
        if view.author_id != (uid or "") and role != "admin" and not view.is_public:
            raise HTTPException(status_code=404, detail="not_found")
        return {
            "id": view.id,
            "slug": view.slug,
            "author_id": view.author_id,
            "title": view.title,
            "tags": view.tags,
            "is_public": view.is_public,
            "status": view.status,
            "publish_at": view.publish_at,
            "unpublish_at": view.unpublish_at,
            "content": view.content_html,
            "cover_url": view.cover_url,
            "embedding": view.embedding,
        }

    @router.get("/slug/{slug}")
    def get_node_by_slug(
        slug: str,
        req: Request,
        container=Depends(get_container),
        claims=Depends(get_current_user),
    ):
        svc = container.nodes_service
        view = svc.get_by_slug(slug)
        if not view:
            raise HTTPException(status_code=404, detail="not_found")
        if str(view.status or "").lower() == "deleted":
            raise HTTPException(status_code=404, detail="not_found")
        uid = str(claims.get("sub")) if claims else None
        role = str(claims.get("role") or "").lower()
        if view.author_id != (uid or "") and role != "admin" and not view.is_public:
            raise HTTPException(status_code=404, detail="not_found")
        return {
            "id": view.id,
            "slug": view.slug,
            "author_id": view.author_id,
            "title": view.title,
            "tags": view.tags,
            "is_public": view.is_public,
            "status": view.status,
            "publish_at": view.publish_at,
            "unpublish_at": view.unpublish_at,
            "content": view.content_html,
            "cover_url": view.cover_url,
            "embedding": view.embedding,
        }

    @router.put("/{node_id}/tags")
    async def set_tags(
        node_id: str,
        body: dict,
        req: Request,
        container=Depends(get_container),
        claims=Depends(get_current_user),
        _csrf: None = Depends(csrf_protect),
    ):
        svc = container.nodes_service
        view, resolved_id = await _resolve_node_ref(node_id, svc)
        if not view or resolved_id is None:
            raise HTTPException(status_code=404, detail="not_found")
        uid = str(claims.get("sub")) if claims else None
        role = str(claims.get("role") or "").lower()
        if view.author_id != (uid or "") and role != "admin":
            raise HTTPException(status_code=403, detail="forbidden")
        try:
            tags = body.get("tags") or []
            if not isinstance(tags, list):
                raise HTTPException(status_code=400, detail="tags_list_required")
            updated = await svc.update_tags(int(resolved_id), tags, actor_id=uid or "")
            return {
                "id": updated.id,
                "tags": updated.tags,
                "embedding": updated.embedding,
            }
        except ValueError as e:
            raise HTTPException(status_code=400, detail=str(e)) from e

    @router.post("")
    async def create_node(
        body: dict,
        req: Request,
        container=Depends(get_container),
        claims=Depends(get_current_user),
        _csrf: None = Depends(csrf_protect),
    ):
        sub = str(claims.get("sub") or "") if claims else ""
        # Normalize author id to UUID: if sub is not UUID, derive stable UUIDv5
        try:
            _uuid.UUID(sub)
            uid = sub
        except Exception:
            uid = str(_uuid.uuid5(_uuid.NAMESPACE_DNS, f"user:{sub}")) if sub else ""
        if not uid:
            raise HTTPException(status_code=401, detail="unauthorized")
        title = body.get("title")
        if title is not None and not isinstance(title, str):
            raise HTTPException(status_code=400, detail="title_invalid")
        tags = body.get("tags") or []
        if not isinstance(tags, list):
            raise HTTPException(status_code=400, detail="tags_list_required")
        is_public = bool(body.get("is_public", False))
        svc = container.nodes_service
        content = body.get("content") or body.get("content_html")
        cover_url = body.get("cover_url")
        status = body.get("status")
        publish_at = body.get("publish_at")
        unpublish_at = body.get("unpublish_at")
        view = await svc.create(
            author_id=uid,
            title=title,
            tags=tags,
            is_public=is_public,
            status=(str(status) if status else None),
            publish_at=(str(publish_at) if publish_at else None),
            unpublish_at=(str(unpublish_at) if unpublish_at else None),
            content_html=content,
            cover_url=cover_url,
        )
        return {
            "id": view.id,
            "slug": view.slug,
            "title": view.title,
            "tags": view.tags,
            "is_public": view.is_public,
            "status": view.status,
            "publish_at": view.publish_at,
            "unpublish_at": view.unpublish_at,
            "content": view.content_html,
            "cover_url": view.cover_url,
            "embedding": view.embedding,
        }

    @router.patch("/{node_id}")
    async def patch_node(
        node_id: str,
        body: dict,
        req: Request,
        container=Depends(get_container),
        claims=Depends(get_current_user),
        _csrf: None = Depends(csrf_protect),
    ):
        svc = container.nodes_service
        view, resolved_id = await _resolve_node_ref(node_id, svc)
        if not view or resolved_id is None:
            raise HTTPException(status_code=404, detail="not_found")
        uid = str(claims.get("sub") or "") if claims else ""
        role = str(claims.get("role") or "").lower()
        if view.author_id != uid and role != "admin":
            raise HTTPException(status_code=403, detail="forbidden")
        title = body.get("title")
        if title is not None and not isinstance(title, str):
            raise HTTPException(status_code=400, detail="title_invalid")
        is_public = body.get("is_public")
        if is_public is not None and not isinstance(is_public, bool):
            raise HTTPException(status_code=400, detail="is_public_invalid")
        status = body.get("status")
        if status is not None and not isinstance(status, str):
            raise HTTPException(status_code=400, detail="status_invalid")
        publish_at = body.get("publish_at") if "publish_at" in body else None
        unpublish_at = body.get("unpublish_at") if "unpublish_at" in body else None
        content = body.get("content") if "content" in body else None
        cover_url = body.get("cover_url") if "cover_url" in body else None
        updated = await svc.update(
            int(resolved_id),
            title=title,
            is_public=is_public,
            status=(str(status) if status is not None else None),
            publish_at=(str(publish_at) if publish_at is not None else None),
            unpublish_at=(str(unpublish_at) if unpublish_at is not None else None),
            content_html=content,
            cover_url=cover_url,
        )
        return {
            "id": updated.id,
            "slug": updated.slug,
            "title": updated.title,
            "is_public": updated.is_public,
            "status": updated.status,
            "publish_at": updated.publish_at,
            "unpublish_at": updated.unpublish_at,
            "content": updated.content_html,
            "cover_url": updated.cover_url,
            "embedding": updated.embedding,
        }

    @router.delete("/{node_id}")
    async def delete_node(
        node_id: str,
        req: Request,
        container=Depends(get_container),
        claims=Depends(get_current_user),
        _csrf: None = Depends(csrf_protect),
    ):
        svc = container.nodes_service
        view, resolved_id = await _resolve_node_ref(node_id, svc)
        if not view or resolved_id is None:
            raise HTTPException(status_code=404, detail="not_found")
        uid = str(claims.get("sub") or "") if claims else ""
        role = str(claims.get("role") or "").lower()
        if view.author_id != uid and role != "admin":
            raise HTTPException(status_code=403, detail="forbidden")
        ok = await svc.delete(int(resolved_id))
        return {"ok": bool(ok)}

    # Saved Views (per-user)
    @router.get("/views")
    async def list_views(
        req: Request,
        container=Depends(get_container),
        claims=Depends(get_current_user),
    ):
        uid = str(claims.get("sub") or "") if claims else ""
        try:
            _uuid.UUID(uid)
        except Exception:
            uid = str(_uuid.uuid5(_uuid.NAMESPACE_DNS, f"user:{uid}")) if uid else ""
        if not uid:
            raise HTTPException(status_code=401, detail="unauthorized")
        eng = await _ensure_engine(container)
        if eng is None:
            return []
        async with eng.begin() as conn:
            rows = (
                (
                    await conn.execute(
                        text(
                            "SELECT name, config, is_default, updated_at FROM product_node_saved_views WHERE user_id = cast(:uid as uuid) ORDER BY is_default DESC, updated_at DESC"
                        ),
                        {"uid": uid},
                    )
                )
                .mappings()
                .all()
            )
        return [
            {
                "name": str(r["name"]),
                "config": r["config"],
                "is_default": bool(r.get("is_default", False)),
                "updated_at": r.get("updated_at"),
            }
            for r in rows
        ]

    @router.post("/views")
    async def upsert_view(
        body: dict,
        req: Request,
        container=Depends(get_container),
        claims=Depends(get_current_user),
        _csrf: None = Depends(csrf_protect),
    ):
        uid = str(claims.get("sub") or "") if claims else ""
        try:
            _uuid.UUID(uid)
        except Exception:
            uid = str(_uuid.uuid5(_uuid.NAMESPACE_DNS, f"user:{uid}")) if uid else ""
        if not uid:
            raise HTTPException(status_code=401, detail="unauthorized")
        name = body.get("name")
        if not isinstance(name, str) or not name.strip():
            raise HTTPException(status_code=400, detail="name_required")
        config = body.get("config")
        if config is None:
            raise HTTPException(status_code=400, detail="config_required")
        # Basic schema validation
        if not isinstance(config, dict):
            raise HTTPException(status_code=400, detail="config_invalid")
        filters = config.get("filters")
        if filters is not None and not isinstance(filters, dict):
            raise HTTPException(status_code=400, detail="filters_invalid")
        if filters:
            if "q" in filters and filters["q"] is not None and not isinstance(filters["q"], str):
                raise HTTPException(status_code=400, detail="filters_q_invalid")
            if (
                "slug" in filters
                and filters["slug"] is not None
                and not isinstance(filters["slug"], str)
            ):
                raise HTTPException(status_code=400, detail="filters_slug_invalid")
            if "status" in filters and filters["status"] is not None:
                st = str(filters["status"]).lower()
                if st not in (
                    "all",
                    "draft",
                    "published",
                    "scheduled",
                    "scheduled_unpublish",
                    "archived",
                    "deleted",
                ):
                    raise HTTPException(status_code=400, detail="filters_status_invalid")
        if "pageSize" in config and config["pageSize"] is not None:
            try:
                ps = int(config["pageSize"])
                if ps < 5 or ps > 200:
                    raise ValueError
            except Exception:
                raise HTTPException(status_code=400, detail="pageSize_invalid") from None
        if "sort" in config and config["sort"] is not None:
            s = str(config["sort"]).lower()
            if s not in ("updated_at", "title", "author", "status"):
                raise HTTPException(status_code=400, detail="sort_invalid")
        if "order" in config and config["order"] is not None:
            o = str(config["order"]).lower()
            if o not in ("asc", "desc"):
                raise HTTPException(status_code=400, detail="order_invalid")
        if (
            "columns" in config
            and config["columns"] is not None
            and not isinstance(config["columns"], dict)
        ):
            raise HTTPException(status_code=400, detail="columns_invalid")
        is_default = bool(body.get("is_default", False))
        eng = await _ensure_engine(container)
        if eng is None:
            raise HTTPException(status_code=500, detail="no_engine")
        async with eng.begin() as conn:
            if is_default:
                await conn.execute(
                    text(
                        "UPDATE product_node_saved_views SET is_default = false WHERE user_id = cast(:uid as uuid) AND is_default = true"
                    ),
                    {"uid": uid},
                )
            await conn.execute(
                text(
                    "INSERT INTO product_node_saved_views(user_id, name, config, is_default) VALUES (cast(:uid as uuid), :name, cast(:config as jsonb), :def) ON CONFLICT (user_id, name) DO UPDATE SET config = EXCLUDED.config, is_default = EXCLUDED.is_default, updated_at = now()"
                ),
                {"uid": uid, "name": name.strip(), "config": config, "def": is_default},
            )
        return {"ok": True}

    @router.delete("/views/{name}")
    async def delete_view(
        name: str,
        req: Request,
        container=Depends(get_container),
        claims=Depends(get_current_user),
        _csrf: None = Depends(csrf_protect),
    ):
        uid = str(claims.get("sub") or "") if claims else ""
        try:
            _uuid.UUID(uid)
        except Exception:
            uid = str(_uuid.uuid5(_uuid.NAMESPACE_DNS, f"user:{uid}")) if uid else ""
        if not uid:
            raise HTTPException(status_code=401, detail="unauthorized")
        eng = await _ensure_engine(container)
        if eng is None:
            raise HTTPException(status_code=500, detail="no_engine")
        async with eng.begin() as conn:
            await conn.execute(
                text(
                    "DELETE FROM product_node_saved_views WHERE user_id = cast(:uid as uuid) AND name = :name"
                ),
                {"uid": uid, "name": name},
            )
        return {"ok": True}

    @router.post("/views/{name}/default")
    async def set_default_view(
        name: str,
        req: Request,
        container=Depends(get_container),
        claims=Depends(get_current_user),
        _csrf: None = Depends(csrf_protect),
    ):
        uid = str(claims.get("sub") or "") if claims else ""
        try:
            _uuid.UUID(uid)
        except Exception:
            uid = str(_uuid.uuid5(_uuid.NAMESPACE_DNS, f"user:{uid}")) if uid else ""
        if not uid:
            raise HTTPException(status_code=401, detail="unauthorized")
        eng = await _ensure_engine(container)
        if eng is None:
            raise HTTPException(status_code=500, detail="no_engine")
        async with eng.begin() as conn:
            await conn.execute(
                text(
                    "UPDATE product_node_saved_views SET is_default = false WHERE user_id = cast(:uid as uuid) AND is_default = true"
                ),
                {"uid": uid},
            )
            await conn.execute(
                text(
                    "UPDATE product_node_saved_views SET is_default = true, updated_at = now() WHERE user_id = cast(:uid as uuid) AND name = :name"
                ),
                {"uid": uid, "name": name},
            )
        return {"ok": True}

    return router

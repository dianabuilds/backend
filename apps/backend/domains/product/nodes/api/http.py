from __future__ import annotations

import logging
import uuid as _uuid
from datetime import UTC, datetime

from fastapi import APIRouter, Depends, HTTPException, Query, Request
from pydantic import ValidationError
from sqlalchemy import text
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncEngine

from apps.backend import get_container
from domains.platform.iam.security import csrf_protect, get_current_user
from packages.core.config import to_async_dsn
from packages.core.db import get_async_engine

logger = logging.getLogger(__name__)


def make_router() -> APIRouter:
    router = APIRouter(prefix="/v1/nodes")

    async def _ensure_engine(container) -> AsyncEngine | None:
        try:
            dsn = to_async_dsn(container.settings.database_url)
        except (ValidationError, ValueError, TypeError) as exc:
            logger.warning("nodes api invalid database configuration", exc_info=exc)
            return None
        if not dsn:
            return None
        if "?" in dsn:
            dsn = dsn.split("?", 1)[0]
        try:
            return get_async_engine("nodes-api", url=dsn, future=True)
        except SQLAlchemyError as exc:
            logger.error("nodes api failed to create engine", exc_info=exc)
            return None

    async def _resolve_node_ref(node_ref: str, svc):
        view = None
        resolved_id: int | None = None
        maybe_id: int | None = None
        try:
            maybe_id = int(node_ref)
        except (TypeError, ValueError):
            maybe_id = None
        if maybe_id is not None:
            dto = await svc._repo_get_async(maybe_id)
            if dto is not None:
                try:
                    resolved_id = int(dto.id)
                except (TypeError, ValueError):
                    resolved_id = None
                else:
                    view = svc._to_view(dto)
        if view is None:
            dto = await svc._repo_get_by_slug_async(str(node_ref))
            if dto is not None:
                try:
                    resolved_id = int(dto.id)
                except (TypeError, ValueError):
                    resolved_id = None
                view = svc._to_view(dto)
        return view, resolved_id

    ROLE_HIERARCHY = {"user": 0, "support": 1, "moderator": 2, "admin": 3}

    def _normalize_actor_id(claims) -> str:
        sub = str((claims or {}).get("sub") or "").strip()
        if not sub:
            return ""
        try:
            _uuid.UUID(sub)
            return sub
        except (ValueError, TypeError):
            try:
                return str(_uuid.uuid5(_uuid.NAMESPACE_DNS, f"user:{sub}"))
            except Exception:
                return ""

    def _get_role(claims) -> str:
        return str((claims or {}).get("role") or "").lower()

    def _has_role(claims, min_role: str) -> bool:
        role = _get_role(claims)
        return ROLE_HIERARCHY.get(role, 0) >= ROLE_HIERARCHY.get(min_role, 0)

    def _parse_request_datetime(raw: str) -> datetime:
        value = raw.strip()
        if value.endswith("Z"):
            value = value[:-1] + "+00:00"
        try:
            parsed = datetime.fromisoformat(value)
        except ValueError as exc:
            raise HTTPException(status_code=400, detail="invalid_timestamp") from exc
        if parsed.tzinfo is None:
            parsed = parsed.replace(tzinfo=UTC)
        return parsed.astimezone(UTC)

    def _view_stat_to_dict(stat) -> dict[str, object]:
        return {
            "node_id": stat.node_id,
            "bucket_date": stat.bucket_date,
            "views": stat.views,
        }

    def _summary_to_dict(summary) -> dict[str, object]:
        return {
            "node_id": summary.node_id,
            "totals": summary.totals,
            "user_reaction": summary.user_reaction,
        }

    def _comment_to_dict(comment) -> dict[str, object]:
        return {
            "id": comment.id,
            "node_id": comment.node_id,
            "author_id": comment.author_id,
            "parent_comment_id": comment.parent_comment_id,
            "depth": comment.depth,
            "content": comment.content,
            "status": comment.status,
            "metadata": comment.metadata,
            "created_at": comment.created_at,
            "updated_at": comment.updated_at,
        }

    def _ban_to_dict(ban) -> dict[str, object]:
        return {
            "node_id": ban.node_id,
            "target_user_id": ban.target_user_id,
            "set_by": ban.set_by,
            "reason": ban.reason,
            "created_at": ban.created_at,
        }

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
            "views_count": view.views_count,
            "reactions_like_count": view.reactions_like_count,
            "comments_disabled": view.comments_disabled,
            "comments_locked_by": view.comments_locked_by,
            "comments_locked_at": view.comments_locked_at,
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
            "views_count": view.views_count,
            "reactions_like_count": view.reactions_like_count,
            "comments_disabled": view.comments_disabled,
            "comments_locked_by": view.comments_locked_by,
            "comments_locked_at": view.comments_locked_at,
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
        except (ValueError, TypeError):
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
            "views_count": updated.views_count,
            "reactions_like_count": updated.reactions_like_count,
            "comments_disabled": updated.comments_disabled,
            "comments_locked_by": updated.comments_locked_by,
            "comments_locked_at": updated.comments_locked_at,
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

    @router.post("/{node_id}/views")
    async def register_view(
        node_id: str,
        req: Request,
        body: dict | None = None,
        container=Depends(get_container),
        claims=Depends(get_current_user),
        _csrf: None = Depends(csrf_protect),
    ):
        svc = container.nodes_service
        view, resolved_id = await _resolve_node_ref(node_id, svc)
        if not view or resolved_id is None:
            raise HTTPException(status_code=404, detail="not_found")
        actor_id = _normalize_actor_id(claims)
        payload = body or {}
        amount = payload.get("amount", 1)
        try:
            amount_int = int(amount)
        except (ValueError, TypeError):
            raise HTTPException(status_code=400, detail="amount_invalid") from None
        fingerprint = payload.get("fingerprint")
        if fingerprint is not None and not isinstance(fingerprint, str):
            raise HTTPException(status_code=400, detail="fingerprint_invalid")
        at_raw = payload.get("at")
        at_dt = None
        if at_raw is not None:
            if not isinstance(at_raw, str):
                raise HTTPException(status_code=400, detail="timestamp_invalid")
            at_dt = _parse_request_datetime(at_raw)
        total = await svc.register_view(
            int(resolved_id),
            viewer_id=actor_id or None,
            fingerprint=str(fingerprint or "") or None,
            amount=amount_int,
            at=at_dt,
        )
        return {"id": resolved_id, "views_count": total}

    @router.get("/{node_id}/views")
    async def get_views(
        node_id: str,
        req: Request,
        container=Depends(get_container),
        claims=Depends(get_current_user),
        limit: int = 30,
        offset: int = 0,
    ):
        svc = container.nodes_service
        view, resolved_id = await _resolve_node_ref(node_id, svc)
        if not view or resolved_id is None:
            raise HTTPException(status_code=404, detail="not_found")
        if limit < 1 or limit > 90:
            raise HTTPException(status_code=400, detail="limit_invalid")
        if offset < 0:
            raise HTTPException(status_code=400, detail="offset_invalid")
        total = await svc.get_total_views(int(resolved_id))
        stats = await svc.get_view_stats(int(resolved_id), limit=limit, offset=offset)
        return {
            "id": resolved_id,
            "total": total,
            "buckets": [_view_stat_to_dict(stat) for stat in stats],
        }

    @router.post("/{node_id}/reactions/like")
    async def add_like(
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
        actor_id = _normalize_actor_id(claims)
        if not actor_id:
            raise HTTPException(status_code=401, detail="unauthorized")
        liked = await svc.add_like(int(resolved_id), user_id=actor_id)
        summary = await svc.get_reactions_summary(int(resolved_id), user_id=actor_id)
        return {
            "id": resolved_id,
            "liked": liked,
            "summary": _summary_to_dict(summary),
        }

    @router.delete("/{node_id}/reactions/like")
    async def remove_like(
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
        actor_id = _normalize_actor_id(claims)
        if not actor_id:
            raise HTTPException(status_code=401, detail="unauthorized")
        removed = await svc.remove_like(int(resolved_id), user_id=actor_id)
        summary = await svc.get_reactions_summary(int(resolved_id), user_id=actor_id)
        return {
            "id": resolved_id,
            "liked": not removed,
            "summary": _summary_to_dict(summary),
        }

    @router.get("/{node_id}/reactions")
    async def get_reactions(
        node_id: str,
        req: Request,
        container=Depends(get_container),
        claims=Depends(get_current_user),
    ):
        svc = container.nodes_service
        view, resolved_id = await _resolve_node_ref(node_id, svc)
        if not view or resolved_id is None:
            raise HTTPException(status_code=404, detail="not_found")
        actor_id = _normalize_actor_id(claims)
        summary = await svc.get_reactions_summary(int(resolved_id), user_id=actor_id or None)
        return _summary_to_dict(summary)

    @router.get("/{node_id}/comments")
    async def list_comments(
        node_id: str,
        req: Request,
        container=Depends(get_container),
        claims=Depends(get_current_user),
        parent_id: int | None = Query(default=None, alias="parentId"),
        limit: int = Query(default=50, ge=1, le=200),
        offset: int = Query(default=0, ge=0),
        include_deleted: bool = Query(default=False, alias="includeDeleted"),
    ):
        svc = container.nodes_service
        view, resolved_id = await _resolve_node_ref(node_id, svc)
        if not view or resolved_id is None:
            raise HTTPException(status_code=404, detail="not_found")
        actor_id = _normalize_actor_id(claims)
        allow_deleted = include_deleted and (
            _has_role(claims, "moderator") or view.author_id == actor_id
        )
        if include_deleted and not allow_deleted:
            raise HTTPException(status_code=403, detail="insufficient_role")
        comments = await svc.list_comments(
            int(resolved_id),
            parent_comment_id=parent_id,
            limit=limit,
            offset=offset,
            include_deleted=allow_deleted,
        )
        return {
            "items": [_comment_to_dict(comment) for comment in comments],
            "count": len(comments),
        }

    @router.post("/{node_id}/comments")
    async def create_comment(
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
        actor_id = _normalize_actor_id(claims)
        if not actor_id:
            raise HTTPException(status_code=401, detail="unauthorized")
        content = body.get("content")
        if not isinstance(content, str) or not content.strip():
            raise HTTPException(status_code=400, detail="content_required")
        parent_comment_id = body.get("parent_comment_id") or body.get("parentId")
        if parent_comment_id is not None:
            try:
                parent_comment_id = int(parent_comment_id)
            except (ValueError, TypeError):
                raise HTTPException(status_code=400, detail="parent_id_invalid") from None
        metadata = body.get("metadata")
        if metadata is not None and not isinstance(metadata, dict):
            raise HTTPException(status_code=400, detail="metadata_invalid")
        try:
            comment = await svc.create_comment(
                node_id=int(resolved_id),
                author_id=actor_id,
                content=content,
                parent_comment_id=parent_comment_id,
                metadata=metadata,
            )
        except ValueError as exc:
            raise HTTPException(status_code=400, detail=str(exc)) from exc
        return _comment_to_dict(comment)

    @router.delete("/comments/{comment_id}")
    async def delete_comment(
        comment_id: int,
        req: Request,
        container=Depends(get_container),
        claims=Depends(get_current_user),
        hard: bool = Query(default=False),
        reason: str | None = Query(default=None),
        _csrf: None = Depends(csrf_protect),
    ):
        svc = container.nodes_service
        comment = await svc.get_comment(comment_id)
        if comment is None:
            raise HTTPException(status_code=404, detail="not_found")
        node_dto = await svc._repo_get_async(comment.node_id)
        if node_dto is None:
            raise HTTPException(status_code=404, detail="node_not_found")
        actor_id = _normalize_actor_id(claims)
        if not actor_id:
            raise HTTPException(status_code=401, detail="unauthorized")
        can_delete = (
            comment.author_id == actor_id
            or node_dto.author_id == actor_id
            or _has_role(claims, "moderator")
        )
        if not can_delete:
            raise HTTPException(status_code=403, detail="forbidden")
        removed = await svc.delete_comment(
            comment_id,
            actor_id=actor_id,
            hard=bool(hard),
            reason=reason,
        )
        return {"ok": bool(removed)}

    @router.patch("/comments/{comment_id}/status")
    async def update_comment_status(
        comment_id: int,
        body: dict,
        req: Request,
        container=Depends(get_container),
        claims=Depends(get_current_user),
        _csrf: None = Depends(csrf_protect),
    ):
        if not _has_role(claims, "moderator"):
            raise HTTPException(status_code=403, detail="insufficient_role")
        status = body.get("status")
        if not isinstance(status, str) or not status.strip():
            raise HTTPException(status_code=400, detail="status_required")
        actor_id = _normalize_actor_id(claims)
        svc = container.nodes_service
        reason = body.get("reason")
        try:
            updated = await svc.update_comment_status(
                comment_id,
                status=status,
                actor_id=actor_id or None,
                reason=reason,
            )
        except ValueError as exc:
            raise HTTPException(status_code=400, detail=str(exc)) from exc
        return _comment_to_dict(updated)

    @router.post("/{node_id}/comments/lock")
    async def toggle_comments_lock(
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
        actor_id = _normalize_actor_id(claims)
        if not actor_id:
            raise HTTPException(status_code=401, detail="unauthorized")
        if view.author_id != actor_id and not _has_role(claims, "moderator"):
            raise HTTPException(status_code=403, detail="forbidden")
        locked = bool(body.get("locked", True))
        reason = body.get("reason")
        if locked:
            await svc.lock_comments(int(resolved_id), actor_id=actor_id, reason=reason)
        else:
            await svc.unlock_comments(int(resolved_id), actor_id=actor_id)
        return {"id": resolved_id, "locked": locked}

    @router.post("/{node_id}/comments/disable")
    async def toggle_comments_disabled(
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
        actor_id = _normalize_actor_id(claims)
        if not actor_id:
            raise HTTPException(status_code=401, detail="unauthorized")
        if view.author_id != actor_id and not _has_role(claims, "moderator"):
            raise HTTPException(status_code=403, detail="forbidden")
        disabled = bool(body.get("disabled", True))
        reason = body.get("reason")
        if disabled:
            await svc.disable_comments(int(resolved_id), actor_id=actor_id, reason=reason)
        else:
            await svc.enable_comments(int(resolved_id), actor_id=actor_id, reason=reason)
        return {"id": resolved_id, "disabled": disabled}

    @router.post("/{node_id}/comments/ban")
    async def ban_comment_user(
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
        actor_id = _normalize_actor_id(claims)
        if not actor_id:
            raise HTTPException(status_code=401, detail="unauthorized")
        if view.author_id != actor_id and not _has_role(claims, "moderator"):
            raise HTTPException(status_code=403, detail="forbidden")
        target_user_id = body.get("target_user_id") or body.get("targetUserId")
        if not isinstance(target_user_id, str) or not target_user_id.strip():
            raise HTTPException(status_code=400, detail="target_user_id_required")
        reason = body.get("reason")
        ban = await svc.ban_comment_user(
            int(resolved_id),
            target_user_id=target_user_id.strip(),
            actor_id=actor_id,
            reason=reason,
        )
        return _ban_to_dict(ban)

    @router.delete("/{node_id}/comments/ban/{target_user_id}")
    async def unban_comment_user(
        node_id: str,
        target_user_id: str,
        req: Request,
        container=Depends(get_container),
        claims=Depends(get_current_user),
        _csrf: None = Depends(csrf_protect),
    ):
        svc = container.nodes_service
        view, resolved_id = await _resolve_node_ref(node_id, svc)
        if not view or resolved_id is None:
            raise HTTPException(status_code=404, detail="not_found")
        actor_id = _normalize_actor_id(claims)
        if not actor_id:
            raise HTTPException(status_code=401, detail="unauthorized")
        if view.author_id != actor_id and not _has_role(claims, "moderator"):
            raise HTTPException(status_code=403, detail="forbidden")
        ok = await svc.unban_comment_user(int(resolved_id), target_user_id=target_user_id)
        return {"ok": bool(ok)}

    @router.get("/{node_id}/comments/bans")
    async def list_comment_bans(
        node_id: str,
        req: Request,
        container=Depends(get_container),
        claims=Depends(get_current_user),
    ):
        svc = container.nodes_service
        view, resolved_id = await _resolve_node_ref(node_id, svc)
        if not view or resolved_id is None:
            raise HTTPException(status_code=404, detail="not_found")
        actor_id = _normalize_actor_id(claims)
        if view.author_id != actor_id and not _has_role(claims, "moderator"):
            raise HTTPException(status_code=403, detail="forbidden")
        bans = await svc.list_comment_bans(int(resolved_id))
        return [_ban_to_dict(ban) for ban in bans]

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
        except (ValueError, TypeError):
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
        except (ValueError, TypeError):
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
            except (TypeError, ValueError):
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
        except (ValueError, TypeError):
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
        except (ValueError, TypeError):
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

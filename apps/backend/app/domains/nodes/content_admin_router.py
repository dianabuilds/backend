# mypy: ignore-errors
from __future__ import annotations

import logging
from datetime import datetime
from typing import Annotated, Literal
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Path, Query
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.domains.nodes.application.editorjs_renderer import (
    collect_unknown_blocks,
    render_html,
)
from app.domains.nodes.application.node_service import NodeService
from app.domains.nodes.infrastructure.models.node import Node
from app.domains.nodes.models import NodeItem
from app.domains.nodes.schemas.node import AdminNodeList, AdminNodeOut
from app.schemas.nodes_common import Status, Visibility
from app.domains.nodes.service import publish_content
from app.domains.users.infrastructure.models.user import User
from app.providers.db.session import get_db
from app.security import ADMIN_AUTH_RESPONSES, auth_user, require_admin_role
# type routes removed; no feature flag needed

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/admin/nodes", tags=["admin"], responses=ADMIN_AUTH_RESPONSES)

# Separate sub-routers to guarantee registration order.
# ``id_router`` is included before ``type_router`` so that requests with a
# single path segment resolve to ID-based handlers before the more generic
# type-based ones.
id_router = APIRouter()
type_router = APIRouter(prefix="/types")


class PublishIn(BaseModel):
    access: Literal["everyone", "premium_only", "early_access"] = "everyone"
    cover: str | None = None
    scheduled_at: datetime | None = None

    model_config = {
        "populate_by_name": True,
        "json_schema_extra": {
            "examples": [
                {"access": "everyone"},
                {"access": "everyone", "scheduled_at": "2025-09-20T10:00:00Z"},
            ]
        },
    }


def _serialize(item: NodeItem, node: Node | None = None) -> dict:
    """Serialize node/item pair into a JSON-friendly dict.

    The redesigned admin UI expects a richer payload than the legacy editor,
    including various flags and timestamps.  We expose both camelCase and
    snake_case keys for backwards compatibility.
    """

    node_data = node or Node(
        id=item.node_id or 0,
        slug=item.slug,
        title=item.title,
        content={},
        author_id=item.created_by_user_id,
        is_public=False,
        is_visible=True,
        allow_feedback=True,
        is_recommendable=True,
        premium_only=False,
        nft_required=None,
        ai_generated=False,
        meta={},
        media=[],
        views=0,
        reactions={},
        popularity_score=0.0,
        created_by_user_id=item.created_by_user_id,
        updated_by_user_id=item.updated_by_user_id,
    )

    node_pk = node.id if node else item.node_id

    # Provide stable defaults so the admin UI can render all controls even when
    # the ``meta`` blob is empty for legacy/imported records.
    editorjs_default = {
        "time": int(__import__("time").time() * 1000),
        "blocks": [],
        "version": "2.30.7",
    }

    raw_content = node_data.content
    if isinstance(raw_content, str):
        try:
            import json as _json

            parsed = _json.loads(raw_content)
        except Exception:
            parsed = None
    else:
        parsed = raw_content

    if isinstance(parsed, list):
        content_value = {
            "time": int(__import__("time").time() * 1000),
            "blocks": parsed,
            "version": "2.30.7",
        }
    elif isinstance(parsed, dict):
        content_value = parsed
    else:
        content_value = editorjs_default

    meta_dict = getattr(node_data, "_meta_dict", lambda: {})().copy()
    meta_dict.pop("content", None)

    payload = {
        "id": node_pk,
        "contentId": item.id,
        "nodeId": node_pk,
        "nodeType": item.type,
        "type": item.type,  # legacy
        "slug": item.slug,
        "title": item.title,
        "subtitle": getattr(node_data, "subtitle", None) or "",
        "summary": item.summary,
        "status": item.status.value,
        "publishedAt": item.published_at.isoformat() if item.published_at else None,
        "scheduledAt": (node_data._meta_dict() or {}).get("scheduled_at"),
        "createdAt": item.created_at.isoformat() if item.created_at else None,
        "updatedAt": item.updated_at.isoformat() if item.updated_at else None,
        # admin editor expects content and cover fields in payload
        "content": content_value,
        # Pre-rendered HTML for preview clients
        "contentHtml": render_html(content_value),
        "coverUrl": node_data.coverUrl if node_data.coverUrl is not None else None,
        "coverAssetId": getattr(node_data, "cover_asset_id", None),
        "coverMeta": getattr(node_data, "cover_meta", None),
        "coverAlt": getattr(node_data, "cover_alt", None) or "",
        "media": node_data.media or [],
        "isPublic": node_data.is_public,
        "isVisible": node_data.is_visible,
        "allowFeedback": node_data.allow_feedback,
        "isRecommendable": node_data.is_recommendable,
        "premiumOnly": node_data.premium_only,
        "nftRequired": node_data.nft_required,
        "aiGenerated": node_data.ai_generated,
        "meta": meta_dict,
        "authorId": str(node_data.author_id) if node_data.author_id else None,
        "createdByUserId": (
            str(node_data.created_by_user_id)
            if node_data.created_by_user_id
            else (str(item.created_by_user_id) if item.created_by_user_id else None)
        ),
        "updatedByUserId": (
            str(node_data.updated_by_user_id)
            if node_data.updated_by_user_id
            else (str(item.updated_by_user_id) if item.updated_by_user_id else None)
        ),
        "views": node_data.views or 0,
        "reactions": node_data.reactions or {},
        "popularityScore": node_data.popularity_score or 0.0,
        # Provide both snake_case and camelCase explicitly
        "tags": node_data.tag_slugs if hasattr(node_data, "tag_slugs") else [],
    }
    # Informational: list unsupported blocks in content to help clients decide
    try:
        payload["unsupportedBlocks"] = collect_unknown_blocks(content_value)
    except Exception:
        payload["unsupportedBlocks"] = []
    return payload


async def _resolve_content_item_id(db: AsyncSession, *, account_id: UUID, node_or_item_id: int) -> NodeItem:
    # 1) Direct NodeItem by id (allow global items)
    item = await db.get(NodeItem, node_or_item_id)
    if item is not None:
        return item

    # 2) Node lookup (tenant or global)
    node = await db.get(Node, node_or_item_id)
    if node is None:
        logger.warning(
            "content_item.node_missing",
            extra={
                "account_id": str(account_id),
                "node_or_item_id": node_or_item_id,
            },
        )
        raise HTTPException(status_code=404, detail="Node not found")

    # Resolve by Node.id and tenant match
    res = await db.execute(select(NodeItem).where(NodeItem.node_id == node.id).order_by(NodeItem.updated_at.desc()))
    item = res.scalar_one_or_none()
    if item is None:
        # Don't backfill for alias/global routes (indicated by UUID(int=0))
        try:
            if getattr(account_id, "int", None) == 0:
                raise HTTPException(status_code=404, detail="Node not found")
        except Exception:
            pass
        # Backfill minimal NodeItem for legacy rows lacking content_items
        item = NodeItem(
            node_id=node.id,
            type="quest",
            slug=node.slug,
            title=node.title or "",
            created_by_user_id=node.created_by_user_id or node.author_id,
            status=Status.draft,
            visibility=Visibility.private,
            version=1,
        )
        db.add(item)
        await db.flush()
        await db.commit()
    return item


@id_router.get("/{node_id}", response_model=AdminNodeOut, summary="Get node item by id")
async def get_node_by_id(
    node_id: Annotated[int, Path(...)],
    _: Annotated[object, Depends(require_admin_role())] = ...,  # noqa: B008
    db: Annotated[AsyncSession, Depends(get_db)] = ...,  # noqa: B008
):
    import time as _t

    t0 = _t.perf_counter()
    node_item = await _resolve_content_item_id(db, node_or_item_id=node_id)
    t_resolve = _t.perf_counter()
    svc = NodeService(db)
    item = await svc.get(node_item.id)
    t_item = _t.perf_counter()
    node = await db.scalar(
        select(Node).where(Node.id == item.node_id).options(selectinload(Node.tags))
    )
    t_node = _t.perf_counter()
    payload = _serialize(item, node)
    t_ser = _t.perf_counter()
    try:
        logger.info(
            "admin.node_timing",
            extra={
                "node_id": item.id,
                "resolve_ms": int((t_resolve - t0) * 1000),
                "item_ms": int((t_item - t_resolve) * 1000),
                "node_ms": int((t_node - t_item) * 1000),
                "serialize_ms": int((t_ser - t_node) * 1000),
                "total_ms": int((t_ser - t0) * 1000),
            },
        )
    except Exception:
        pass
    return payload


@id_router.patch("/{node_id}", response_model=AdminNodeOut, summary="Update node item by id")
async def update_node_by_id(
    node_id: Annotated[int, Path(...)],
    payload: dict,
    next: Annotated[int, Query()] = 0,
    _: Annotated[object, Depends(require_admin_role())] = ...,  # noqa: B008
    current_user: Annotated[User, Depends(auth_user)] = ...,  # noqa: B008
    db: Annotated[AsyncSession, Depends(get_db)] = ...,  # noqa: B008
):
    node_item = await _resolve_content_item_id(db, node_or_item_id=node_id)
    svc = NodeService(db)
    item = await svc.update(
        node_item.id,
        payload,
        actor_id=current_user.id,
    )
    if next:
        from app.domains.telemetry.application.ux_metrics_facade import ux_metrics

        ux_metrics.inc_save_next()
    node = await db.scalar(
        select(Node).where(Node.id == item.node_id).options(selectinload(Node.tags))
    )
    return _serialize(item, node)


@id_router.put("/{node_id}", response_model=AdminNodeOut, summary="Replace node item by id")
async def replace_node_by_id(
    node_id: Annotated[int, Path(...)],
    payload: dict,
    next: Annotated[int, Query()] = 0,
    _: Annotated[object, Depends(require_admin_role())] = ...,  # noqa: B008
    current_user: Annotated[User, Depends(auth_user)] = ...,  # noqa: B008
    db: Annotated[AsyncSession, Depends(get_db)] = ...,  # noqa: B008,
):
    node_item = await _resolve_content_item_id(db, node_or_item_id=node_id)
    svc = NodeService(db)
    item = await svc.update(
        node_item.id,
        payload,
        actor_id=current_user.id,
    )
    if next:
        from app.domains.telemetry.application.ux_metrics_facade import ux_metrics

        ux_metrics.inc_save_next()
    node = await db.scalar(
        select(Node).where(Node.id == item.node_id).options(selectinload(Node.tags))
    )
    return _serialize(item, node)


@id_router.post(
    "/{node_id}/publish",
    response_model=AdminNodeOut,
    summary="Publish node item by id",
)
async def publish_node_by_id(
    node_id: Annotated[int, Path(...)],
    payload: PublishIn | None = None,
    _: Annotated[object, Depends(require_admin_role())] = ...,  # noqa: B008
    current_user: Annotated[User, Depends(auth_user)] = ...,  # noqa: B008
    db: Annotated[AsyncSession, Depends(get_db)] = ...,  # noqa: B008
):
    node_item = await _resolve_content_item_id(db, node_or_item_id=node_id)
    svc = NodeService(db)
    item = await svc.publish(
        node_item.id,
        actor_id=current_user.id,
        access=(payload.access if payload else "everyone"),
        scheduled_at=(payload.scheduled_at if payload else None),
    )
    await publish_content(node_id=item.id, slug=item.slug, author_id=current_user.id)
    node = await db.scalar(select(Node).where(Node.id == item.node_id))
    return _serialize(item, node)


@type_router.get("/{node_type}", response_model=AdminNodeList, summary="List nodes by type")
async def list_nodes(
    node_type: str,
    account_id: Annotated[UUID, Path(...)],  # noqa: B008
    page: int = 1,
    per_page: int = 10,
    q: str | None = None,
    _: Annotated[object, Depends(require_admin_role())] = ...,  # noqa: B008
    db: Annotated[AsyncSession, Depends(get_db)] = ...,  # noqa: B008
):
    if str(node_type).lower() in ("quest", "quests"):
        raise HTTPException(
            status_code=422,
            detail="quest nodes are read-only; use /quests/*",
        )
    svc = NodeService(db)
    if q:
        items = await svc.search(q, page=page, per_page=per_page)
    else:
        items = await svc.list(page=page, per_page=per_page)
    return {"items": [_serialize(i) for i in items]}


@type_router.post("/{node_type}", response_model=AdminNodeOut, summary="Create node item")
async def create_node(
    node_type: str,
    account_id: Annotated[UUID, Path(...)],  # noqa: B008
    _: Annotated[object, Depends(require_admin_role())] = ...,  # noqa: B008
    current_user: Annotated[User, Depends(auth_user)] = ...,  # noqa: B008
    db: Annotated[AsyncSession, Depends(get_db)] = ...,  # noqa: B008
):
    if str(node_type).lower() in ("quest", "quests"):
        raise HTTPException(
            status_code=422,
            detail="quest nodes are read-only; use /quests/*",
        )
    svc = NodeService(db)
    item = await svc.create(actor_id=current_user.id)
    node = await db.get(Node, item.node_id or item.id, options=(selectinload(Node.tags),))
    return _serialize(item, node)


@type_router.get(
    "/{node_type}/{node_id}",
    response_model=AdminNodeOut,
    summary="Get node item",
)
async def get_node(
    node_type: str,
    node_id: Annotated[int, Path(...)],
    account_id: Annotated[UUID, Path(...)],  # noqa: B008
    _: Annotated[object, Depends(require_admin_role())] = ...,  # noqa: B008
    db: Annotated[AsyncSession, Depends(get_db)] = ...,  # noqa: B008
):
    if str(node_type).lower() in ("quest", "quests"):
        raise HTTPException(
            status_code=422,
            detail="quest nodes are read-only; use /quests/*",
        )
    node_item = await _resolve_content_item_id(db, account_id=account_id, node_or_item_id=node_id)
    svc = NodeService(db)
    item = await svc.get(node_item.id)
    node = await db.get(Node, item.node_id or item.id, options=(selectinload(Node.tags),))
    return _serialize(item, node)


@type_router.patch(
    "/{node_type}/{node_id}",
    response_model=AdminNodeOut,
    summary="Update node item",
)
async def update_node(
    node_type: str,
    node_id: Annotated[int, Path(...)],
    payload: dict,
    account_id: Annotated[UUID, Path(...)],  # noqa: B008
    next: Annotated[int, Query()] = 0,
    current_user: Annotated[User, Depends(auth_user)] = ...,  # noqa: B008
    db: Annotated[AsyncSession, Depends(get_db)] = ...,  # noqa: B008
):
    if str(node_type).lower() in ("quest", "quests"):
        raise HTTPException(
            status_code=422,
            detail="quest nodes are read-only; use /quests/*",
        )

    node_item = await _resolve_content_item_id(db, account_id=account_id, node_or_item_id=node_id)
    svc = NodeService(db)
    item = await svc.update(
        node_item.id,
        payload,
        actor_id=current_user.id,
    )
    if next:
        from app.domains.telemetry.application.ux_metrics_facade import ux_metrics

        ux_metrics.inc_save_next()
    node = await db.get(Node, item.node_id or item.id, options=(selectinload(Node.tags),))
    return _serialize(item, node)


@type_router.post(
    "/{node_type}/{node_id}/publish",
    response_model=AdminNodeOut,
    summary="Publish node item",
)
async def publish_node(
    node_type: str,
    node_id: Annotated[int, Path(...)],
    account_id: Annotated[UUID, Path(...)],  # noqa: B008
    payload: PublishIn | None = None,
    _: Annotated[object, Depends(require_admin_role())] = ...,  # noqa: B008
    current_user: Annotated[User, Depends(auth_user)] = ...,  # noqa: B008
    db: Annotated[AsyncSession, Depends(get_db)] = ...,  # noqa: B008
):
    if str(node_type).lower() in ("quest", "quests"):
        raise HTTPException(
            status_code=422,
            detail="quest nodes are read-only; use /quests/*",
        )
    node_item = await _resolve_content_item_id(db, account_id=account_id, node_or_item_id=node_id)
    svc = NodeService(db)
    item = await svc.publish(
        node_item.id,
        actor_id=current_user.id,
        access=(payload.access if payload else "everyone"),
        scheduled_at=(payload.scheduled_at if payload else None),
    )
    await publish_content(node_id=item.id, slug=item.slug, author_id=current_user.id)
    node = await db.get(Node, item.node_id or item.id)
    return _serialize(item, node)


# PATCH-алиас на случай, если фронт отправляет PATCH вместо POST
@type_router.patch(
    "/{node_type}/{node_id}/publish",
    response_model=AdminNodeOut,
    summary="Publish node item (PATCH alias)",
)
async def publish_node_patch(
    node_type: str,
    node_id: Annotated[int, Path(...)],
    account_id: Annotated[UUID, Path(...)],  # noqa: B008
    payload: PublishIn | None = None,
    _: Annotated[object, Depends(require_admin_role())] = ...,  # noqa: B008
    current_user: Annotated[User, Depends(auth_user)] = ...,  # noqa: B008
    db: Annotated[AsyncSession, Depends(get_db)] = ...,  # noqa: B008
):
    if str(node_type).lower() in ("quest", "quests"):
        raise HTTPException(
            status_code=422,
            detail="quest nodes are read-only; use /quests/*",
        )
    node_item = await _resolve_content_item_id(db, account_id=account_id, node_or_item_id=node_id)
    svc = NodeService(db)
    item = await svc.publish(
        node_item.id,
        actor_id=current_user.id,
        access=(payload.access if payload else "everyone"),
    )
    await publish_content(node_id=item.id, slug=item.slug, author_id=current_user.id)
    node = await db.get(Node, item.node_id or item.id)
    return _serialize(item, node)


# Register sub-routers in the desired order.
router.include_router(id_router)



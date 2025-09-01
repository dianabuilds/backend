# mypy: ignore-errors
from __future__ import annotations

from typing import Annotated, Literal
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Path, Query
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.db.session import get_db
from app.domains.nodes.application.node_service import NodeService
from app.domains.nodes.infrastructure.models.node import Node
from app.domains.nodes.models import NodeItem
from app.domains.nodes.service import publish_content
from app.domains.users.infrastructure.models.user import User
from app.security import ADMIN_AUTH_RESPONSES, auth_user, require_ws_editor

router = APIRouter(
    prefix="/admin/workspaces/{workspace_id}/nodes",
    tags=["admin"],
    responses=ADMIN_AUTH_RESPONSES,
)

# Separate sub-routers to guarantee registration order.
# ``id_router`` is included before ``type_router`` so that requests with a
# single path segment resolve to ID-based handlers before the more generic
# type-based ones.
id_router = APIRouter()
type_router = APIRouter(prefix="/types")


class PublishIn(BaseModel):
    access: Literal["everyone", "premium_only", "early_access"] = "everyone"
    cover: str | None = None


def _serialize(item: NodeItem, node: Node | None = None) -> dict:
    """Serialize node/item pair into a JSON-friendly dict.

    The redesigned admin UI expects a richer payload than the legacy editor,
    including various flags and timestamps.  We expose both camelCase and
    snake_case keys for backwards compatibility.
    """

    node_data = node or Node(
        id=item.node_id or 0,
        workspace_id=item.workspace_id,
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

    return {
        "id": node_pk,
        "contentId": item.id,
        "nodeId": node_pk,
        "workspace_id": str(item.workspace_id),
        "nodeType": item.type,
        "type": item.type,  # legacy
        "slug": item.slug,
        "title": item.title,
        "summary": item.summary,
        "status": item.status.value,
        "publishedAt": item.published_at.isoformat() if item.published_at else None,
        "createdAt": item.created_at.isoformat() if item.created_at else None,
        "updatedAt": item.updated_at.isoformat() if item.updated_at else None,
        # admin editor expects content and coverUrl in payload
        "content": node_data.content,
        "coverUrl": node_data.cover_url,
        "media": node_data.media,
        "isPublic": node_data.is_public,
        "isVisible": node_data.is_visible,
        "allowFeedback": node_data.allow_feedback,
        "isRecommendable": node_data.is_recommendable,
        "premiumOnly": node_data.premium_only,
        "nftRequired": node_data.nft_required,
        "aiGenerated": node_data.ai_generated,
        "meta": node_data.meta,
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
        "views": node_data.views,
        "reactions": node_data.reactions or {},
        "popularityScore": node_data.popularity_score,
        "tag_slugs": node_data.tag_slugs if hasattr(node_data, "tag_slugs") else [],
        "tags": node_data.tag_slugs if hasattr(node_data, "tag_slugs") else [],
    }


async def _resolve_content_item_id(
    db: AsyncSession, *, workspace_id: UUID, node_or_item_id: int
) -> int:
    """Resolve ``NodeItem.id`` from either ``Node.id`` or ``NodeItem.id``.

    ``node_or_item_id`` may be a numeric ``Node.id`` used by newer clients or a
    ``NodeItem.id`` from legacy callers.
    """

    item = await db.get(NodeItem, node_or_item_id)
    if item is not None and item.workspace_id == workspace_id:
        return item.id

    res = await db.execute(
        select(NodeItem.id)
        .where(
            NodeItem.workspace_id == workspace_id, NodeItem.node_id == node_or_item_id
        )
        .order_by(NodeItem.updated_at.desc())
    )
    content_id = res.scalar_one_or_none()
    if content_id is not None:
        return content_id

    raise HTTPException(status_code=404, detail="Node not found")


@id_router.get("/{node_id}", summary="Get node item by id")
async def get_node_by_id(
    node_id: Annotated[int, Path(...)],
    workspace_id: Annotated[UUID, Path(...)],  # noqa: B008
    _: Annotated[object, Depends(require_ws_editor)] = ...,  # noqa: B008
    db: Annotated[AsyncSession, Depends(get_db)] = ...,  # noqa: B008
):
    content_id = await _resolve_content_item_id(
        db, workspace_id=workspace_id, node_or_item_id=node_id
    )
    svc = NodeService(db)
    item = await svc.get(workspace_id, content_id)
    node = await db.scalar(
        select(Node).where(Node.id == item.node_id).options(selectinload(Node.tags))
    )
    return _serialize(item, node)


@id_router.patch("/{node_id}", summary="Update node item by id")
async def update_node_by_id(
    node_id: Annotated[int, Path(...)],
    payload: dict,
    workspace_id: Annotated[UUID, Path(...)],  # noqa: B008
    next: Annotated[int, Query()] = 0,
    _: Annotated[object, Depends(require_ws_editor)] = ...,  # noqa: B008
    current_user: Annotated[User, Depends(auth_user)] = ...,  # noqa: B008
    db: Annotated[AsyncSession, Depends(get_db)] = ...,  # noqa: B008
):
    content_id = await _resolve_content_item_id(
        db, workspace_id=workspace_id, node_or_item_id=node_id
    )
    svc = NodeService(db)
    item = await svc.update(
        workspace_id,
        content_id,
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


@id_router.put("/{node_id}", summary="Replace node item by id")
async def replace_node_by_id(
    node_id: Annotated[int, Path(...)],
    payload: dict,
    workspace_id: Annotated[UUID, Path(...)],  # noqa: B008
    next: Annotated[int, Query()] = 0,
    _: Annotated[object, Depends(require_ws_editor)] = ...,  # noqa: B008
    current_user: Annotated[User, Depends(auth_user)] = ...,  # noqa: B008
    db: Annotated[AsyncSession, Depends(get_db)] = ...,  # noqa: B008,
):
    content_id = await _resolve_content_item_id(
        db, workspace_id=workspace_id, node_or_item_id=node_id
    )
    svc = NodeService(db)
    item = await svc.update(
        workspace_id,
        content_id,
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


@id_router.post("/{node_id}/publish", summary="Publish node item by id")
async def publish_node_by_id(
    node_id: Annotated[int, Path(...)],
    workspace_id: Annotated[UUID, Path(...)],  # noqa: B008
    payload: PublishIn | None = None,
    _: Annotated[object, Depends(require_ws_editor)] = ...,  # noqa: B008
    current_user: Annotated[User, Depends(auth_user)] = ...,  # noqa: B008
    db: Annotated[AsyncSession, Depends(get_db)] = ...,  # noqa: B008
):
    content_id = await _resolve_content_item_id(
        db, workspace_id=workspace_id, node_or_item_id=node_id
    )
    svc = NodeService(db)
    item = await svc.publish(
        workspace_id,
        content_id,
        actor_id=current_user.id,
        access=(payload.access if payload else "everyone"),
    )
    await publish_content(
        node_id=item.id,
        slug=item.slug,
        author_id=current_user.id,
        workspace_id=workspace_id,
    )
    node = await db.scalar(select(Node).where(Node.id == item.node_id))
    return _serialize(item, node)


@type_router.get("/{node_type}", summary="List nodes by type")
async def list_nodes(
    node_type: str,
    workspace_id: Annotated[UUID, Path(...)],  # noqa: B008
    page: int = 1,
    per_page: int = 10,
    q: str | None = None,
    _: Annotated[object, Depends(require_ws_editor)] = ...,  # noqa: B008
    db: Annotated[AsyncSession, Depends(get_db)] = ...,  # noqa: B008
):
    if str(node_type).lower() in ("quest", "quests"):
        raise HTTPException(
            status_code=422,
            detail="quest nodes are read-only; use /quests/*",
        )
    svc = NodeService(db)
    if q:
        items = await svc.search(workspace_id, q, page=page, per_page=per_page)
    else:
        items = await svc.list(workspace_id, page=page, per_page=per_page)
    return {"items": [_serialize(i) for i in items]}


@type_router.post("/{node_type}", summary="Create node item")
async def create_node(
    node_type: str,
    workspace_id: Annotated[UUID, Path(...)],  # noqa: B008
    _: Annotated[object, Depends(require_ws_editor)] = ...,  # noqa: B008
    current_user: Annotated[User, Depends(auth_user)] = ...,  # noqa: B008
    db: Annotated[AsyncSession, Depends(get_db)] = ...,  # noqa: B008
):
    if str(node_type).lower() in ("quest", "quests"):
        raise HTTPException(
            status_code=422,
            detail="quest nodes are read-only; use /quests/*",
        )
    svc = NodeService(db)
    item = await svc.create(workspace_id, actor_id=current_user.id)
    node = await db.get(
        Node, item.node_id or item.id, options=(selectinload(Node.tags),)
    )
    return _serialize(item, node)


@type_router.get("/{node_type}/{node_id}", summary="Get node item")
async def get_node(
    node_type: str,
    node_id: Annotated[int, Path(...)],
    workspace_id: Annotated[UUID, Path(...)],  # noqa: B008
    _: Annotated[object, Depends(require_ws_editor)] = ...,  # noqa: B008
    db: Annotated[AsyncSession, Depends(get_db)] = ...,  # noqa: B008
):
    if str(node_type).lower() in ("quest", "quests"):
        raise HTTPException(
            status_code=422,
            detail="quest nodes are read-only; use /quests/*",
        )
    content_id = await _resolve_content_item_id(
        db, workspace_id=workspace_id, node_or_item_id=node_id
    )
    svc = NodeService(db)
    item = await svc.get(workspace_id, content_id)
    node = await db.get(
        Node, item.node_id or item.id, options=(selectinload(Node.tags),)
    )
    return _serialize(item, node)


@type_router.patch("/{node_type}/{node_id}", summary="Update node item")
async def update_node(
    node_type: str,
    node_id: Annotated[int, Path(...)],
    payload: dict,
    workspace_id: Annotated[UUID, Path(...)],  # noqa: B008
    next: Annotated[int, Query()] = 0,
    _: Annotated[object, Depends(require_ws_editor)] = ...,  # noqa: B008
    current_user: Annotated[User, Depends(auth_user)] = ...,  # noqa: B008
    db: Annotated[AsyncSession, Depends(get_db)] = ...,  # noqa: B008
):
    if str(node_type).lower() in ("quest", "quests"):
        raise HTTPException(
            status_code=422,
            detail="quest nodes are read-only; use /quests/*",
        )

    content_id = await _resolve_content_item_id(
        db, workspace_id=workspace_id, node_or_item_id=node_id
    )
    svc = NodeService(db)
    item = await svc.update(
        workspace_id,
        content_id,
        payload,
        actor_id=current_user.id,
    )
    if next:
        from app.domains.telemetry.application.ux_metrics_facade import ux_metrics

        ux_metrics.inc_save_next()
    node = await db.get(
        Node, item.node_id or item.id, options=(selectinload(Node.tags),)
    )
    return _serialize(item, node)


@type_router.post("/{node_type}/{node_id}/publish", summary="Publish node item")
async def publish_node(
    node_type: str,
    node_id: Annotated[int, Path(...)],
    workspace_id: Annotated[UUID, Path(...)],  # noqa: B008
    payload: PublishIn | None = None,
    _: Annotated[object, Depends(require_ws_editor)] = ...,  # noqa: B008
    current_user: Annotated[User, Depends(auth_user)] = ...,  # noqa: B008
    db: Annotated[AsyncSession, Depends(get_db)] = ...,  # noqa: B008
):
    if str(node_type).lower() in ("quest", "quests"):
        raise HTTPException(
            status_code=422,
            detail="quest nodes are read-only; use /quests/*",
        )
    content_id = await _resolve_content_item_id(
        db, workspace_id=workspace_id, node_or_item_id=node_id
    )
    svc = NodeService(db)
    item = await svc.publish(
        workspace_id,
        content_id,
        actor_id=current_user.id,
        access=(payload.access if payload else "everyone"),
    )
    await publish_content(
        node_id=item.id,
        slug=item.slug,
        author_id=current_user.id,
        workspace_id=workspace_id,
    )
    node = await db.get(Node, item.node_id or item.id)
    return _serialize(item, node)


# PATCH-алиас на случай, если фронт отправляет PATCH вместо POST
@type_router.patch(
    "/{node_type}/{node_id}/publish",
    summary="Publish node item (PATCH alias)",
)
async def publish_node_patch(
    node_type: str,
    node_id: Annotated[int, Path(...)],
    workspace_id: Annotated[UUID, Path(...)],  # noqa: B008
    payload: PublishIn | None = None,
    _: Annotated[object, Depends(require_ws_editor)] = ...,  # noqa: B008
    current_user: Annotated[User, Depends(auth_user)] = ...,  # noqa: B008
    db: Annotated[AsyncSession, Depends(get_db)] = ...,  # noqa: B008
):
    if str(node_type).lower() in ("quest", "quests"):
        raise HTTPException(
            status_code=422,
            detail="quest nodes are read-only; use /quests/*",
        )
    content_id = await _resolve_content_item_id(
        db, workspace_id=workspace_id, node_or_item_id=node_id
    )
    svc = NodeService(db)
    item = await svc.publish(
        workspace_id,
        content_id,
        actor_id=current_user.id,
        access=(payload.access if payload else "everyone"),
    )
    await publish_content(
        node_id=item.id,
        slug=item.slug,
        author_id=current_user.id,
        workspace_id=workspace_id,
    )
    node = await db.get(Node, item.node_id or item.id)
    return _serialize(item, node)


# Register sub-routers in the desired order.
router.include_router(id_router)
router.include_router(type_router)

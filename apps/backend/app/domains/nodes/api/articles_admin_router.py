from __future__ import annotations

from typing import Annotated, Literal
from uuid import UUID

from fastapi import APIRouter, Depends, Path, Query
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.domains.nodes.application.node_service import NodeService
from app.domains.nodes.infrastructure.models.node import Node
from app.domains.nodes.models import NodeItem
from app.domains.nodes.service import publish_content
from app.providers.db.session import get_db
from app.security import ADMIN_AUTH_RESPONSES, require_admin_role

router = APIRouter(
    prefix="/admin/workspaces/{workspace_id}/articles",
    tags=["admin"],
    responses=ADMIN_AUTH_RESPONSES,
)

admin_required = require_admin_role()


class PublishIn(BaseModel):
    access: Literal["everyone", "premium_only", "early_access"] = "everyone"
    cover: str | None = None


def _serialize(item: NodeItem, node: Node | None = None) -> dict:
    """Serialize node item along with infrastructure node data.

    The admin UI expects content, tags and various flags to be included in the
    response.  Legacy articles might not have a corresponding ``Node`` row, in
    which case we provide sensible defaults to avoid missing values in the UI.
    """

    node_data = node or Node(
        id=item.id,
        account_id=item.workspace_id,
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

    return {
        "id": item.id,
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
        "content": node_data.content,
        "coverUrl": node_data.coverUrl,
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
        "tags": node_data.tag_slugs if hasattr(node_data, "tag_slugs") else [],
    }


@router.post("", summary="Create article (admin)")
async def create_article(
    workspace_id: Annotated[UUID, Path(...)],  # noqa: B008
    payload: dict | None = None,
    current_user=Depends(admin_required),  # noqa: B008
    db: Annotated[AsyncSession, Depends(get_db)] = ...,  # noqa: B008
):
    svc = NodeService(db)
    item = await svc.create(workspace_id, actor_id=current_user.id)
    node = await db.get(Node, item.node_id or item.id, options=(selectinload(Node.tags),))
    return _serialize(item, node)


@router.get("/{node_id}", summary="Get article (admin)")
async def get_article(
    node_id: int,
    workspace_id: Annotated[UUID, Path(...)],  # noqa: B008
    current_user=Depends(admin_required),  # noqa: B008
    db: Annotated[AsyncSession, Depends(get_db)] = ...,  # noqa: B008
):
    svc = NodeService(db)
    item = await svc.get(workspace_id, node_id)
    node = await db.get(Node, item.node_id or item.id, options=(selectinload(Node.tags),))
    return _serialize(item, node)


@router.patch("/{node_id}", summary="Update article (admin)")
async def update_article(
    node_id: int,
    payload: dict,
    workspace_id: Annotated[UUID, Path(...)],  # noqa: B008
    next: Annotated[int, Query()] = 0,
    current_user=Depends(admin_required),  # noqa: B008
    db: Annotated[AsyncSession, Depends(get_db)] = ...,  # noqa: B008
):
    svc = NodeService(db)
    item = await svc.update(
        workspace_id,
        node_id,
        payload,
        actor_id=current_user.id,
    )
    if next:
        from app.domains.telemetry.application.ux_metrics_facade import ux_metrics

        ux_metrics.inc_save_next()
    node = await db.get(Node, item.node_id or item.id, options=(selectinload(Node.tags),))
    return _serialize(item, node)


@router.post("/{node_id}/publish", summary="Publish article (admin)")
async def publish_article(
    node_id: int,
    workspace_id: Annotated[UUID, Path(...)],  # noqa: B008
    payload: PublishIn | None = None,
    current_user=Depends(admin_required),  # noqa: B008
    db: Annotated[AsyncSession, Depends(get_db)] = ...,  # noqa: B008
):
    svc = NodeService(db)
    item = await svc.publish(
        workspace_id,
        node_id,
        actor_id=current_user.id,
        access=(payload.access if payload else "everyone"),
    )
    await publish_content(
        node_id=item.id,
        slug=item.slug,
        author_id=current_user.id,
        workspace_id=workspace_id,
    )
    node = await db.get(Node, item.node_id or item.id, options=(selectinload(Node.tags),))
    return _serialize(item, node)

from __future__ import annotations

from typing import Literal
from uuid import UUID

from fastapi import APIRouter, Depends, Path, Query
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.db.session import get_db
from app.domains.nodes.application.node_service import NodeService
from app.domains.nodes.models import NodeItem
from app.domains.nodes.service import publish_content
from app.domains.users.infrastructure.models.user import User
from app.schemas.nodes_common import NodeType
from app.security import ADMIN_AUTH_RESPONSES, auth_user, require_ws_editor

router = APIRouter(
    prefix="/admin/workspaces/{workspace_id}/articles",
    tags=["admin"],
    responses=ADMIN_AUTH_RESPONSES,
)


class PublishIn(BaseModel):
    access: Literal["everyone", "premium_only", "early_access"] = "everyone"
    cover: str | None = None


def _serialize(item: NodeItem) -> dict:
    return {
        "id": str(item.id),
        "workspace_id": str(item.workspace_id),
        "type": item.type,
        "slug": item.slug,
        "title": item.title,
        "summary": item.summary,
        "status": item.status.value,
    }


@router.get("", summary="List articles")
async def list_articles(
    workspace_id: UUID = Path(...),  # noqa: B008
    page: int = 1,
    per_page: int = 10,
    q: str | None = None,
    _: object = Depends(require_ws_editor),  # noqa: B008
    db: AsyncSession = Depends(get_db),  # noqa: B008
):
    svc = NodeService(db)
    if q:
        items = await svc.search(
            workspace_id, NodeType.article, q, page=page, per_page=per_page
        )
    else:
        items = await svc.list(
            workspace_id, NodeType.article, page=page, per_page=per_page
        )
    return {"items": [_serialize(i) for i in items]}


@router.post("", summary="Create article")
async def create_article(
    workspace_id: UUID = Path(...),  # noqa: B008
    _: object = Depends(require_ws_editor),  # noqa: B008
    current_user: User = Depends(auth_user),  # noqa: B008
    db: AsyncSession = Depends(get_db),  # noqa: B008
):
    svc = NodeService(db)
    item = await svc.create(workspace_id, NodeType.article, actor_id=current_user.id)
    return _serialize(item)


@router.get("/{node_id}", summary="Get article")
async def get_article(
    node_id: UUID,
    workspace_id: UUID = Path(...),  # noqa: B008
    _: object = Depends(require_ws_editor),  # noqa: B008
    db: AsyncSession = Depends(get_db),  # noqa: B008
):
    svc = NodeService(db)
    item = await svc.get(workspace_id, NodeType.article, node_id)
    return _serialize(item)


@router.patch("/{node_id}", summary="Update article")
async def update_article(
    node_id: UUID,
    payload: dict,
    workspace_id: UUID = Path(...),  # noqa: B008
    next: int = Query(0),
    _: object = Depends(require_ws_editor),  # noqa: B008
    current_user: User = Depends(auth_user),  # noqa: B008
    db: AsyncSession = Depends(get_db),  # noqa: B008
):
    svc = NodeService(db)
    item = await svc.update(
        workspace_id,
        NodeType.article,
        node_id,
        payload,
        actor_id=current_user.id,
    )
    if next:
        from app.domains.telemetry.application.ux_metrics_facade import ux_metrics

        ux_metrics.inc_save_next()
    return _serialize(item)


@router.post("/{node_id}/publish", summary="Publish article")
async def publish_article(
    node_id: UUID,
    workspace_id: UUID = Path(...),  # noqa: B008
    payload: PublishIn | None = None,
    _: object = Depends(require_ws_editor),  # noqa: B008
    current_user: User = Depends(auth_user),  # noqa: B008
    db: AsyncSession = Depends(get_db),  # noqa: B008
):
    svc = NodeService(db)
    item = await svc.publish(
        workspace_id,
        NodeType.article,
        node_id,
        actor_id=current_user.id,
        access=(payload.access if payload else "everyone"),
        cover=(payload.cover if payload else None),
    )
    await publish_content(
        node_id=item.id,
        slug=item.slug,
        author_id=current_user.id,
        workspace_id=workspace_id,
    )
    return _serialize(item)

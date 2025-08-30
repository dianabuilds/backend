from typing import Literal
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Path, Query
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.db.session import get_db
from app.domains.nodes.application.node_service import NodeService
from app.domains.nodes.models import NodeItem
from app.domains.nodes.service import publish_content
from app.domains.users.infrastructure.models.user import User
from app.domains.nodes.infrastructure.models.node import Node
from app.security import ADMIN_AUTH_RESPONSES, auth_user, require_ws_editor

router = APIRouter(
    prefix="/admin/workspaces/{workspace_id}/nodes",
    tags=["admin"],
    responses=ADMIN_AUTH_RESPONSES,
)


class PublishIn(BaseModel):
    access: Literal["everyone", "premium_only", "early_access"] = "everyone"
    cover: str | None = None


def _serialize(item: NodeItem, node: Node | None = None) -> dict:
    return {
        "id": str(item.id),
        "workspace_id": str(item.workspace_id),
        "type": item.type,
        "slug": item.slug,
        "title": item.title,
        "summary": item.summary,
        "status": item.status.value,
        # admin editor expects content and coverUrl in payload
        "content": (node.content if node is not None else None),
        "coverUrl": (node.cover_url if node is not None else None),
        "tag_slugs": (node.tag_slugs if node is not None else []),
        "tags": (node.tag_slugs if node is not None else []),
    }


@router.get("/{node_type}", summary="List nodes by type")
async def list_nodes(
    node_type: str,
    workspace_id: UUID = Path(...),
    page: int = 1,
    per_page: int = 10,
    q: str | None = None,
    _: object = Depends(require_ws_editor),  # noqa: B008
    db: AsyncSession = Depends(get_db),  # noqa: B008
):
    if str(node_type).lower() in ("quest", "quests"):
        raise HTTPException(
            status_code=422,
            detail="quest nodes are read-only; use /quests/*",
        )
    svc = NodeService(db)
    if q:
        items = await svc.search(
            workspace_id, node_type, q, page=page, per_page=per_page
        )
    else:
        items = await svc.list(workspace_id, node_type, page=page, per_page=per_page)
    return {"items": [_serialize(i) for i in items]}


@router.post("/{node_type}", summary="Create node item")
async def create_node(
    node_type: str,
    workspace_id: UUID = Path(...),
    _: object = Depends(require_ws_editor),  # noqa: B008
    current_user: User = Depends(auth_user),  # noqa: B008
    db: AsyncSession = Depends(get_db),  # noqa: B008
):
    if str(node_type).lower() in ("quest", "quests"):
        raise HTTPException(
            status_code=422,
            detail="quest nodes are read-only; use /quests/*",
        )
    svc = NodeService(db)
    item = await svc.create(workspace_id, node_type, actor_id=current_user.id)
    node = await db.get(Node, item.id, options=(selectinload(Node.tags),))
    return _serialize(item, node)


@router.get("/{node_type}/{node_id}", summary="Get node item")
async def get_node(
    node_type: str,
    node_id: UUID,
    workspace_id: UUID = Path(...),
    _: object = Depends(require_ws_editor),  # noqa: B008
    db: AsyncSession = Depends(get_db),  # noqa: B008
):
    if str(node_type).lower() in ("quest", "quests"):
        raise HTTPException(
            status_code=422,
            detail="quest nodes are read-only; use /quests/*",
        )
    svc = NodeService(db)
    item = await svc.get(workspace_id, node_type, node_id)
    node = await db.get(Node, item.id, options=(selectinload(Node.tags),))
    return _serialize(item, node)


@router.patch("/{node_type}/{node_id}", summary="Update node item")
async def update_node(
    node_type: str,
    node_id: UUID,
    payload: dict,
    workspace_id: UUID = Path(...),
    next: int = Query(0),
    _: object = Depends(require_ws_editor),  # noqa: B008
    current_user: User = Depends(auth_user),  # noqa: B008
    db: AsyncSession = Depends(get_db),  # noqa: B008
):
    if str(node_type).lower() in ("quest", "quests"):
        raise HTTPException(
            status_code=422,
            detail="quest nodes are read-only; use /quests/*",
        )

    svc = NodeService(db)
    item = await svc.update(
        workspace_id,
        node_type,
        node_id,
        payload,
        actor_id=current_user.id,
    )
    if next:
        from app.domains.telemetry.application.ux_metrics_facade import ux_metrics

        ux_metrics.inc_save_next()
    node = await db.get(Node, item.id, options=(selectinload(Node.tags),))
    return _serialize(item, node)


@router.post("/{node_type}/{node_id}/publish", summary="Publish node item")
async def publish_node(
    node_type: str,
    node_id: UUID,
    workspace_id: UUID = Path(...),
    payload: PublishIn | None = None,
    _: object = Depends(require_ws_editor),  # noqa: B008
    current_user: User = Depends(auth_user),  # noqa: B008
    db: AsyncSession = Depends(get_db),  # noqa: B008
):
    if str(node_type).lower() in ("quest", "quests"):
        raise HTTPException(
            status_code=422,
            detail="quest nodes are read-only; use /quests/*",
        )
    svc = NodeService(db)
    item = await svc.publish(
        workspace_id,
        node_type,
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
    node = await db.get(Node, item.id)
    return _serialize(item, node)


# PATCH-алиас на случай, если фронт отправляет PATCH вместо POST
@router.patch("/{node_type}/{node_id}/publish", summary="Publish node item (PATCH alias)")
async def publish_node_patch(
    node_type: str,
    node_id: UUID,
    workspace_id: UUID = Path(...),
    payload: PublishIn | None = None,
    _: object = Depends(require_ws_editor),  # noqa: B008
    current_user: User = Depends(auth_user),  # noqa: B008
    db: AsyncSession = Depends(get_db),  # noqa: B008
):
    if str(node_type).lower() in ("quest", "quests"):
        raise HTTPException(
            status_code=422,
            detail="quest nodes are read-only; use /quests/*",
        )
    svc = NodeService(db)
    item = await svc.publish(
        workspace_id,
        node_type,
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
    node = await db.get(Node, item.id)
    return _serialize(item, node)

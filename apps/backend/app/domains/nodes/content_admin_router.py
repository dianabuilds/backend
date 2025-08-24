from typing import Literal
from uuid import UUID

from fastapi import APIRouter, Depends, Query, Request
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.db.session import get_db
from app.domains.navigation.application.navigation_cache_service import (
    NavigationCacheService,
)
from app.domains.navigation.infrastructure.cache_adapter import CoreCacheAdapter
from app.domains.nodes.application.node_service import NodeService
from app.domains.nodes.models import NodeItem
from app.domains.users.infrastructure.models.user import User
from app.schemas.nodes_common import NodeType
from app.schemas.quest_editor import SimulateIn
from app.security import ADMIN_AUTH_RESPONSES, auth_user, require_ws_editor

router = APIRouter(
    prefix="/admin/nodes",
    tags=["admin"],
    responses=ADMIN_AUTH_RESPONSES,
)

navcache = NavigationCacheService(CoreCacheAdapter())


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


@router.get("", summary="List nodes")
async def list_nodes(
    workspace_id: UUID,
    node_type: NodeType = Query(..., alias="type"),  # noqa: B008
    page: int = 1,
    per_page: int = 10,
    q: str | None = None,
    _: object = Depends(require_ws_editor),  # noqa: B008
    db: AsyncSession = Depends(get_db),  # noqa: B008
):
    svc = NodeService(db, navcache)
    if q:
        items = await svc.search(
            workspace_id, node_type, q, page=page, per_page=per_page
        )
    else:
        items = await svc.list(workspace_id, node_type, page=page, per_page=per_page)
    return {"items": [_serialize(i) for i in items]}


@router.post("/{node_type}", summary="Create node item")
async def create_node(
    node_type: NodeType,
    workspace_id: UUID,
    _: object = Depends(require_ws_editor),  # noqa: B008
    current_user: User = Depends(auth_user),  # noqa: B008
    db: AsyncSession = Depends(get_db),  # noqa: B008
):
    svc = NodeService(db, navcache)
    item = await svc.create(workspace_id, node_type, actor_id=current_user.id)
    return _serialize(item)


@router.get("/{node_type}/{node_id}", summary="Get node item")
async def get_node(
    node_type: NodeType,
    node_id: UUID,
    workspace_id: UUID,
    _: object = Depends(require_ws_editor),  # noqa: B008
    db: AsyncSession = Depends(get_db),  # noqa: B008
):
    svc = NodeService(db, navcache)
    item = await svc.get(workspace_id, node_type, node_id)
    return _serialize(item)


@router.patch("/{node_type}/{node_id}", summary="Update node item")
async def update_node(
    node_type: NodeType,
    node_id: UUID,
    workspace_id: UUID,
    request: Request,
    payload: dict,
    _: object = Depends(require_ws_editor),  # noqa: B008
    current_user: User = Depends(auth_user),  # noqa: B008
    db: AsyncSession = Depends(get_db),  # noqa: B008
):
    svc = NodeService(db, navcache)
    item = await svc.update(
        workspace_id,
        node_type,
        node_id,
        payload,
        actor_id=current_user.id,
        request=request,
    )
    return _serialize(item)


@router.post("/{node_type}/{node_id}/publish", summary="Publish node item")
async def publish_node(
    node_type: NodeType,
    node_id: UUID,
    workspace_id: UUID,
    request: Request,
    payload: PublishIn | None = None,
    _: object = Depends(require_ws_editor),  # noqa: B008
    current_user: User = Depends(auth_user),  # noqa: B008
    db: AsyncSession = Depends(get_db),  # noqa: B008
):
    svc = NodeService(db, navcache)
    item = await svc.publish(
        workspace_id,
        node_type,
        node_id,
        actor_id=current_user.id,
        access=(payload.access if payload else "everyone"),
        cover=(payload.cover if payload else None),
        request=request,
    )
    return _serialize(item)


@router.post("/{node_type}/{node_id}/validate", summary="Validate node item")
async def validate_node_item(
    node_type: NodeType,
    node_id: UUID,
    workspace_id: UUID,
    _: object = Depends(require_ws_editor),  # noqa: B008
    db: AsyncSession = Depends(get_db),  # noqa: B008
):
    svc = NodeService(db, navcache)
    report = await svc.validate(node_type, node_id)
    return {"report": report}


@router.post("/{node_type}/{node_id}/simulate", summary="Simulate quest node")
async def simulate_node(
    node_type: NodeType,
    node_id: UUID,
    workspace_id: UUID,
    payload: SimulateIn,
    _: object = Depends(require_ws_editor),  # noqa: B008
    db: AsyncSession = Depends(get_db),  # noqa: B008
):
    svc = NodeService(db, navcache)
    report, result = await svc.simulate(workspace_id, node_type, node_id, payload)
    return {"report": report, "result": result}

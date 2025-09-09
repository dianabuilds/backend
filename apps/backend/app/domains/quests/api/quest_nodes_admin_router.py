from __future__ import annotations

from typing import Literal
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, Request
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from app.providers.db.session import get_db
from app.domains.nodes.application.node_service import NodeService
from app.domains.nodes.models import NodeItem
from app.domains.navigation.application.navigation_cache_service import (
    NavigationCacheService,
)
from app.domains.navigation.infrastructure.cache_adapter import CoreCacheAdapter
from app.domains.notifications.infrastructure.in_app_port import InAppNotificationPort
from app.domains.users.infrastructure.models.user import User
from app.schemas.nodes_common import NodeType
from app.security import ADMIN_AUTH_RESPONSES, require_admin_role


router = APIRouter(
    prefix="/admin/quests/{quest_id}/nodes",
    tags=["admin-quest-nodes"],
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


@router.get("", summary="List quest nodes")
async def list_quest_nodes(
    quest_id: UUID,  # noqa: ARG001 - reserved for stricter checks later
    workspace_id: UUID | None = Query(default=None),
    tenant_id: UUID | None = Query(default=None),
    page: int = 1,
    per_page: int = 10,
    q: str | None = None,
    current_user: User = Depends(require_admin_role()),  # noqa: B008
    db: AsyncSession = Depends(get_db),  # noqa: B008
):
    svc = NodeService(db, navcache, InAppNotificationPort(db))
    node_type = NodeType.quest
    ws = tenant_id or workspace_id
    if ws is None:
        raise HTTPException(status_code=400, detail="tenant_id is required")
    if q:
        items = await svc.search(
            ws, node_type, q, page=page, per_page=per_page
        )
    else:
        items = await svc.list(ws, node_type, page=page, per_page=per_page)
    return {"items": [_serialize(i) for i in items]}


@router.post("", summary="Create quest node")
async def create_quest_node(
    quest_id: UUID,  # noqa: ARG001 - reserved
    workspace_id: UUID | None = Query(default=None),
    tenant_id: UUID | None = Query(default=None),
    current_user: User = Depends(require_admin_role()),  # noqa: B008
    db: AsyncSession = Depends(get_db),  # noqa: B008
):
    svc = NodeService(db, navcache, InAppNotificationPort(db))
    ws = tenant_id or workspace_id
    if ws is None:
        raise HTTPException(status_code=400, detail="tenant_id is required")
    item = await svc.create(ws, NodeType.quest, actor_id=current_user.id)
    return _serialize(item)


@router.get("/{node_id}", summary="Get quest node")
async def get_quest_node(
    quest_id: UUID,  # noqa: ARG001 - reserved
    node_id: UUID,
    workspace_id: UUID | None = Query(default=None),
    tenant_id: UUID | None = Query(default=None),
    current_user: User = Depends(require_admin_role()),  # noqa: B008
    db: AsyncSession = Depends(get_db),  # noqa: B008
):
    svc = NodeService(db, navcache, InAppNotificationPort(db))
    ws = tenant_id or workspace_id
    if ws is None:
        raise HTTPException(status_code=400, detail="tenant_id is required")
    item = await svc.get(ws, NodeType.quest, node_id)
    if not item:
        raise HTTPException(status_code=404, detail="Not found")
    return _serialize(item)


@router.patch("/{node_id}", summary="Update quest node")
async def update_quest_node(
    quest_id: UUID,  # noqa: ARG001 - reserved
    node_id: UUID,
    workspace_id: UUID | None = Query(default=None),
    tenant_id: UUID | None = Query(default=None),
    request: Request,
    payload: dict,
    next: int = Query(0),
    current_user: User = Depends(require_admin_role()),  # noqa: B008
    db: AsyncSession = Depends(get_db),  # noqa: B008
):
    svc = NodeService(db, navcache, InAppNotificationPort(db))
    ws = tenant_id or workspace_id
    if ws is None:
        raise HTTPException(status_code=400, detail="tenant_id is required")
    item = await svc.update(
        ws,
        NodeType.quest,
        node_id,
        payload,
        actor_id=current_user.id,
        request=request,
    )
    return _serialize(item)


@router.post("/{node_id}/publish", summary="Publish quest node")
async def publish_quest_node(
    quest_id: UUID,  # noqa: ARG001 - reserved
    node_id: UUID,
    workspace_id: UUID | None = Query(default=None),
    tenant_id: UUID | None = Query(default=None),
    request: Request,
    payload: PublishIn | None = None,
    current_user: User = Depends(require_admin_role()),  # noqa: B008
    db: AsyncSession = Depends(get_db),  # noqa: B008
):
    svc = NodeService(db, navcache, InAppNotificationPort(db))
    ws = tenant_id or workspace_id
    if ws is None:
        raise HTTPException(status_code=400, detail="tenant_id is required")
    item = await svc.publish(
        ws,
        NodeType.quest,
        node_id,
        actor_id=current_user.id,
        access=(payload.access if payload else "everyone"),
        cover=(payload.cover if payload else None),
        request=request,
    )
    return _serialize(item)


@router.post("/{node_id}/validate", summary="Validate quest node")
async def validate_quest_node(
    quest_id: UUID,  # noqa: ARG001 - reserved
    node_id: UUID,
    workspace_id: UUID | None = Query(default=None),
    tenant_id: UUID | None = Query(default=None),
    current_user: User = Depends(require_admin_role()),  # noqa: B008
    db: AsyncSession = Depends(get_db),  # noqa: B008
):
    svc = NodeService(db, navcache, InAppNotificationPort(db))
    ws = tenant_id or workspace_id
    if ws is None:
        raise HTTPException(status_code=400, detail="tenant_id is required")
    report = await svc.validate(ws, NodeType.quest, node_id)
    blocking = [item for item in report.items if item.level == "error"]
    warnings = [item for item in report.items if item.level == "warning"]
    return {"report": report, "blocking": blocking, "warnings": warnings}


@router.post("/{node_id}/simulate", summary="Simulate quest node")
async def simulate_quest_node(
    quest_id: UUID,  # noqa: ARG001 - reserved
    node_id: UUID,
    workspace_id: UUID | None = Query(default=None),
    tenant_id: UUID | None = Query(default=None),
    payload: dict,
    current_user: User = Depends(require_admin_role()),  # noqa: B008
    db: AsyncSession = Depends(get_db),  # noqa: B008
):
    svc = NodeService(db, navcache, InAppNotificationPort(db))
    from app.schemas.quest_editor import SimulateIn

    ws = tenant_id or workspace_id
    if ws is None:
        raise HTTPException(status_code=400, detail="tenant_id is required")
    report, result = await svc.simulate(ws, NodeType.quest, node_id, SimulateIn(**payload))
    return {"report": report, "result": result}

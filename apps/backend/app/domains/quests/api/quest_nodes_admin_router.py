from __future__ import annotations

from typing import Literal
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, Request
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.db.session import get_db
from app.domains.nodes.application.node_service import NodeService
from app.domains.nodes.models import NodeItem
from app.domains.navigation.application.navigation_cache_service import (
    NavigationCacheService,
)
from app.domains.navigation.infrastructure.cache_adapter import CoreCacheAdapter
from app.domains.notifications.infrastructure.in_app_port import InAppNotificationPort
from app.domains.users.infrastructure.models.user import User
from app.schemas.nodes_common import NodeType
from app.security import ADMIN_AUTH_RESPONSES, auth_user, require_ws_editor


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
    workspace_id: UUID,
    page: int = 1,
    per_page: int = 10,
    q: str | None = None,
    _: object = Depends(require_ws_editor),  # noqa: B008
    db: AsyncSession = Depends(get_db),  # noqa: B008
):
    svc = NodeService(db, navcache, InAppNotificationPort(db))
    node_type = NodeType.quest
    if q:
        items = await svc.search(
            workspace_id, node_type, q, page=page, per_page=per_page
        )
    else:
        items = await svc.list(workspace_id, node_type, page=page, per_page=per_page)
    return {"items": [_serialize(i) for i in items]}


@router.post("", summary="Create quest node")
async def create_quest_node(
    quest_id: UUID,  # noqa: ARG001 - reserved
    workspace_id: UUID,
    _: object = Depends(require_ws_editor),  # noqa: B008
    current_user: User = Depends(auth_user),  # noqa: B008
    db: AsyncSession = Depends(get_db),  # noqa: B008
):
    svc = NodeService(db, navcache, InAppNotificationPort(db))
    item = await svc.create(workspace_id, NodeType.quest, actor_id=current_user.id)
    return _serialize(item)


@router.get("/{node_id}", summary="Get quest node")
async def get_quest_node(
    quest_id: UUID,  # noqa: ARG001 - reserved
    node_id: UUID,
    workspace_id: UUID,
    _: object = Depends(require_ws_editor),  # noqa: B008
    db: AsyncSession = Depends(get_db),  # noqa: B008
):
    svc = NodeService(db, navcache, InAppNotificationPort(db))
    item = await svc.get(workspace_id, NodeType.quest, node_id)
    if not item:
        raise HTTPException(status_code=404, detail="Not found")
    return _serialize(item)


@router.patch("/{node_id}", summary="Update quest node")
async def update_quest_node(
    quest_id: UUID,  # noqa: ARG001 - reserved
    node_id: UUID,
    workspace_id: UUID,
    request: Request,
    payload: dict,
    next: int = Query(0),
    _: object = Depends(require_ws_editor),  # noqa: B008
    current_user: User = Depends(auth_user),  # noqa: B008
    db: AsyncSession = Depends(get_db),  # noqa: B008
):
    svc = NodeService(db, navcache, InAppNotificationPort(db))
    item = await svc.update(
        workspace_id,
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
    workspace_id: UUID,
    request: Request,
    payload: PublishIn | None = None,
    _: object = Depends(require_ws_editor),  # noqa: B008
    current_user: User = Depends(auth_user),  # noqa: B008
    db: AsyncSession = Depends(get_db),  # noqa: B008
):
    svc = NodeService(db, navcache, InAppNotificationPort(db))
    item = await svc.publish(
        workspace_id,
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
    workspace_id: UUID,
    _: object = Depends(require_ws_editor),  # noqa: B008
    db: AsyncSession = Depends(get_db),  # noqa: B008
):
    svc = NodeService(db, navcache, InAppNotificationPort(db))
    report = await svc.validate(workspace_id, NodeType.quest, node_id)
    blocking = [item for item in report.items if item.level == "error"]
    warnings = [item for item in report.items if item.level == "warning"]
    return {"report": report, "blocking": blocking, "warnings": warnings}


@router.post("/{node_id}/simulate", summary="Simulate quest node")
async def simulate_quest_node(
    quest_id: UUID,  # noqa: ARG001 - reserved
    node_id: UUID,
    workspace_id: UUID,
    payload: dict,
    _: object = Depends(require_ws_editor),  # noqa: B008
    db: AsyncSession = Depends(get_db),  # noqa: B008
):
    svc = NodeService(db, navcache, InAppNotificationPort(db))
    from app.schemas.quest_editor import SimulateIn

    report, result = await svc.simulate(
        workspace_id, NodeType.quest, node_id, SimulateIn(**payload)
    )
    return {"report": report, "result": result}


from __future__ import annotations

from datetime import datetime
from typing import Literal, TypedDict
from uuid import UUID

from fastapi import APIRouter, Depends, Header, Path, Query, Response
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

from app.core.db.session import get_db
from app.core.log_events import cache_invalidate
from app.domains.navigation.application.navigation_cache_service import (
    NavigationCacheService,
)
from app.domains.navigation.application.navigation_service import NavigationService
from app.domains.navigation.infrastructure.cache_adapter import CoreCacheAdapter
from app.domains.nodes.application.node_query_service import NodeQueryService
from app.domains.nodes.application.node_service import NodeService
from app.domains.nodes.application.query_models import (
    NodeFilterSpec,
    PageRequest,
    QueryContext,
)
from app.domains.nodes.infrastructure.models.node import Node
from app.domains.nodes.models import NodeItem
from app.domains.nodes.schemas.node import NodeBulkOperation, NodeBulkPatch, NodeOut
from app.domains.workspaces.infrastructure.models import Workspace
from app.schemas.workspaces import WorkspaceType
from app.security import ADMIN_AUTH_RESPONSES, require_admin_role

router = APIRouter(
    prefix="/admin/workspaces/{workspace_id}/nodes",
    tags=["admin"],
    responses=ADMIN_AUTH_RESPONSES,
)
admin_required = require_admin_role()

navcache = NavigationCacheService(CoreCacheAdapter())
navsvc = NavigationService()


class NodeCreateIn(BaseModel):
    node_type: str


def _serialize(item: NodeItem) -> dict:
    return {
        "id": str(item.id),
        "workspace_id": str(item.workspace_id),
        "node_type": item.type,
        "slug": item.slug,
        "title": item.title,
        "summary": item.summary,
        "status": item.status.value,
    }


class AdminNodeListParams(TypedDict, total=False):
    author: UUID
    sort: Literal[
        "updated_desc",
        "created_desc",
        "created_asc",
        "views_desc",
    ]
    visible: bool
    premium_only: bool
    recommendable: bool
    node_type: str
    limit: int
    offset: int
    date_from: datetime
    date_to: datetime
    q: str


@router.get("", response_model=list[NodeOut], summary="List nodes (admin)")
async def list_nodes_admin(
    response: Response,
    workspace_id: UUID = Path(...),  # noqa: B008
    if_none_match: str | None = Header(None, alias="If-None-Match"),
    author: UUID | None = None,
    sort: Literal[
        "updated_desc",
        "created_desc",
        "created_asc",
        "views_desc",
    ] = Query("updated_desc"),
    visible: bool | None = None,
    premium_only: bool | None = None,
    recommendable: bool | None = None,
    node_type: str | None = Query(None, alias="node_type"),
    limit: int = Query(25, ge=1, le=100),
    offset: int = Query(0, ge=0),
    date_from: datetime | None = None,
    date_to: datetime | None = None,
    q: str | None = None,
    current_user=Depends(admin_required),  # noqa: B008
    db: AsyncSession = Depends(get_db),  # noqa: B008
):
    """List nodes in workspace.

    See :class:`AdminNodeListParams` for available query parameters.
    """
    spec_workspace_id = workspace_id
    workspace = await db.get(Workspace, workspace_id)
    if workspace and workspace.is_system and workspace.type == WorkspaceType.global_:
        spec_workspace_id = None
    spec = NodeFilterSpec(
        workspace_id=spec_workspace_id,
        author_id=author,
        is_visible=visible,
        premium_only=premium_only,
        recommendable=recommendable,
        node_type=node_type,
        created_from=date_from,
        created_to=date_to,
        q=q,
        sort=sort,
    )
    ctx = QueryContext(user=current_user, is_admin=True)
    svc = NodeQueryService(db)
    page = PageRequest(limit=limit, offset=offset)
    etag = await svc.compute_nodes_etag(spec, ctx, page)
    nodes = await svc.list_nodes(spec, page, ctx)
    try:
        response.headers["ETag"] = etag
    except Exception:
        pass
    return nodes


@router.post("", summary="Create node (admin)")
async def create_node_admin(
    payload: NodeCreateIn,
    workspace_id: UUID = Path(...),  # noqa: B008
    current_user=Depends(admin_required),  # noqa: B008
    db: AsyncSession = Depends(get_db),  # noqa: B008
):
    svc = NodeService(db)
    item = await svc.create(workspace_id, payload.node_type, actor_id=current_user.id)
    return _serialize(item)


@router.post("/bulk", summary="Bulk node operations")
async def bulk_node_operation(
    payload: NodeBulkOperation,
    workspace_id: UUID = Path(...),  # noqa: B008
    current_user=Depends(admin_required),  # noqa: B008
    db: AsyncSession = Depends(get_db),  # noqa: B008
):
    result = await db.execute(
        select(Node).where(Node.id.in_(payload.ids), Node.workspace_id == workspace_id)
    )
    nodes = result.scalars().all()
    invalidate_slugs: list[str] = []
    for node in nodes:
        changed = False
        if payload.op == "hide":
            if node.is_visible:
                node.is_visible = False
                changed = True
        elif payload.op == "show":
            if not node.is_visible:
                node.is_visible = True
                changed = True
        elif payload.op == "toggle_premium":
            node.premium_only = not node.premium_only
        elif payload.op == "toggle_recommendable":
            node.is_recommendable = not node.is_recommendable
        if changed:
            invalidate_slugs.append(node.slug)
            await navsvc.invalidate_navigation_cache(db, node)
        node.updated_at = datetime.utcnow()
        node.updated_by_user_id = current_user.id
    await db.commit()
    for slug in invalidate_slugs:
        await navcache.invalidate_navigation_by_node(slug)
        await navcache.invalidate_modes_by_node(slug)
        cache_invalidate("nav", reason="node_bulk", key=slug)
        cache_invalidate("navm", reason="node_bulk", key=slug)
    if invalidate_slugs:
        await navcache.invalidate_compass_all()
        cache_invalidate("comp", reason="node_bulk")
    return {"updated": [str(n.id) for n in nodes]}


@router.patch("/bulk", summary="Bulk update nodes")
async def bulk_patch_nodes(
    payload: NodeBulkPatch,
    workspace_id: UUID = Path(...),  # noqa: B008
    current_user=Depends(admin_required),  # noqa: B008
    db: AsyncSession = Depends(get_db),  # noqa: B008
):
    result = await db.execute(
        select(Node).where(Node.id.in_(payload.ids), Node.workspace_id == workspace_id)
    )
    nodes = result.scalars().all()
    updated_ids: list[str] = []
    deleted_ids: list[str] = []
    invalidate_slugs: list[str] = []
    for node in nodes:
        changes = payload.changes
        if changes.delete:
            invalidate_slugs.append(node.slug)
            deleted_ids.append(str(node.id))
            try:
                await navsvc.invalidate_navigation_cache(db, node)
            except Exception:
                pass
            await db.delete(node)
            continue
        was_visible = node.is_visible
        if changes.is_visible is not None:
            node.is_visible = changes.is_visible
        if changes.premium_only is not None:
            node.premium_only = changes.premium_only
        if changes.is_recommendable is not None:
            node.is_recommendable = changes.is_recommendable
        if changes.workspace_id is not None:
            node.workspace_id = changes.workspace_id
        node.updated_at = datetime.utcnow()
        node.updated_by_user_id = current_user.id
        updated_ids.append(str(node.id))
        if (
            (changes.is_visible is not None and changes.is_visible != was_visible)
            or changes.workspace_id is not None
        ):
            invalidate_slugs.append(node.slug)
            try:
                await navsvc.invalidate_navigation_cache(db, node)
            except Exception:
                pass
    await db.commit()
    for slug in invalidate_slugs:
        await navcache.invalidate_navigation_by_node(slug)
        await navcache.invalidate_modes_by_node(slug)
        cache_invalidate("nav", reason="node_bulk_patch", key=slug)
        cache_invalidate("navm", reason="node_bulk_patch", key=slug)
    if invalidate_slugs:
        await navcache.invalidate_compass_all()
        cache_invalidate("comp", reason="node_bulk_patch")
    return {"updated": updated_ids, "deleted": deleted_ids}

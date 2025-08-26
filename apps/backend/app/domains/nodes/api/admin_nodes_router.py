from __future__ import annotations

from datetime import datetime
from uuid import UUID

from fastapi import APIRouter, Depends, Header, Query, Response
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

from app.core.db.session import get_db
from app.core.log_events import cache_invalidate
from app.domains.navigation.application.navigation_cache_service import (
    NavigationCacheService,
)
from app.domains.navigation.infrastructure.cache_adapter import CoreCacheAdapter
from app.domains.nodes.application.node_query_service import NodeQueryService
from app.domains.nodes.application.query_models import (
    NodeFilterSpec,
    PageRequest,
    QueryContext,
)
from app.domains.nodes.infrastructure.models.node import Node
from app.domains.nodes.schemas.node import NodeBulkOperation, NodeOut
from app.domains.workspaces.infrastructure.models import Workspace
from app.schemas.workspaces import WorkspaceType
from app.security import ADMIN_AUTH_RESPONSES, require_admin_role

router = APIRouter(
    prefix="/admin/nodes", tags=["admin"], responses=ADMIN_AUTH_RESPONSES
)
admin_required = require_admin_role()

navcache = NavigationCacheService(CoreCacheAdapter())


@router.get("", response_model=list[NodeOut], summary="List nodes (admin)")
async def list_nodes_admin(
    response: Response,
    workspace_id: UUID,
    if_none_match: str | None = Header(None, alias="If-None-Match"),
    author: UUID | None = None,
    tags: str | None = Query(None),
    match: str = Query("any", pattern="^(any|all)$"),
    is_public: bool | None = None,
    visible: bool | None = None,
    premium_only: bool | None = None,
    recommendable: bool | None = None,
    limit: int = Query(25, ge=1, le=100),
    offset: int = Query(0, ge=0),
    date_from: datetime | None = None,
    date_to: datetime | None = None,
    q: str | None = None,
    current_user=Depends(admin_required),  # noqa: B008
    db: AsyncSession = Depends(get_db),  # noqa: B008
):
    tag_list = [t.strip() for t in tags.split(",") if t.strip()] if tags else None
    spec_workspace_id = workspace_id
    workspace = await db.get(Workspace, workspace_id)
    if workspace and workspace.is_system and workspace.type == WorkspaceType.global_:
        spec_workspace_id = None
    spec = NodeFilterSpec(
        workspace_id=spec_workspace_id,
        author_id=author,
        tags=tag_list,
        match=match,
        is_public=is_public,
        is_visible=visible,
        premium_only=premium_only,
        recommendable=recommendable,
        created_from=date_from,
        created_to=date_to,
        q=q,
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


@router.post("/bulk", summary="Bulk node operations")
async def bulk_node_operation(
    payload: NodeBulkOperation,
    workspace_id: UUID,
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
        elif payload.op == "public":
            if not node.is_public:
                node.is_public = True
                changed = True
        elif payload.op == "private":
            if node.is_public:
                node.is_public = False
                changed = True
        elif payload.op == "toggle_premium":
            node.premium_only = not node.premium_only
        elif payload.op == "toggle_recommendable":
            node.is_recommendable = not node.is_recommendable
        if changed:
            invalidate_slugs.append(node.slug)
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

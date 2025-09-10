from __future__ import annotations

from datetime import datetime
from typing import Annotated, Literal
from uuid import UUID

from fastapi import APIRouter, Body, Depends, Header, HTTPException, Query
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

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
from app.domains.nodes.content_admin_router import (
    _resolve_content_item_id,
    _serialize,
)
from app.domains.nodes.infrastructure.models.node import Node
from app.domains.nodes.infrastructure.repositories.node_repository import (
    NodeRepository,
)
from app.domains.nodes.models import NodePublishJob
from app.domains.nodes.schemas.node import NodeBulkPatch, NodeOut
from app.domains.users.infrastructure.models.user import User
from app.providers.db.session import get_db
from app.schemas.nodes_common import Status
from app.security import ADMIN_AUTH_RESPONSES, auth_user, require_admin_role

router = APIRouter(prefix="/admin/nodes", tags=["admin"], responses=ADMIN_AUTH_RESPONSES)
admin_required = require_admin_role()

navcache = NavigationCacheService(CoreCacheAdapter())
navsvc = NavigationService()
@router.get("", response_model=list[NodeOut], summary="List nodes (admin, alias)")
async def list_nodes_admin_alias(
    if_none_match: Annotated[str | None, Header(alias="If-None-Match")] = None,
    author: UUID | None = None,
    sort: Annotated[
        Literal["updated_desc", "created_desc", "created_asc", "views_desc"],
        Query(),
    ] = "updated_desc",
    status: Annotated[Status | None, Query()] = None,
    visible: bool | None = None,
    premium_only: bool | None = None,
    recommendable: bool | None = None,
    limit: Annotated[int, Query(ge=1, le=100)] = 25,
    offset: Annotated[int, Query(ge=0)] = 0,
    date_from: datetime | None = None,
    date_to: datetime | None = None,
    q: str | None = None,
    scope_mode: Annotated[
        str | None,
        Query(regex="^(mine|member|invited|space:[0-9]+|global)$"),
    ] = None,
    current_user=Depends(admin_required),  # noqa: B008
    db: Annotated[AsyncSession, Depends(get_db)] = ...,  # noqa: B008
):
    if scope_mode is None:
        scope_mode = "mine"
    spec = NodeFilterSpec(
        author_id=author,
        is_visible=visible,
        premium_only=premium_only,
        recommendable=recommendable,
        created_from=date_from,
        created_to=date_to,
        q=q,
        sort=sort,
        status=status,
    )
    ctx = QueryContext(user=current_user, is_admin=True)
    svc = NodeQueryService(db)
    page = PageRequest(limit=limit, offset=offset)
    await svc.compute_nodes_etag(spec, ctx, page, scope_mode=scope_mode)
    nodes = await svc.list_nodes(spec, page, ctx, scope_mode=scope_mode)
    # We intentionally don't set the ETag header here since FastAPI response isn't passed in; the
    # generated OpenAPI types still work without it. Client-side cache can be layered later.
    return nodes


@router.post("", summary="Create node (admin, alias)")
async def create_node_admin_alias(
    payload: dict | None = Body(default=None),  # noqa: B008
    current_user=Depends(admin_required),  # noqa: B008
    db: Annotated[AsyncSession, Depends(get_db)] = ...,  # noqa: B008
):
    svc = NodeService(db)
    item = await svc.create_personal(actor_id=current_user.id)
    if payload:
        try:
            item = await svc.update_personal(item.id, payload, actor_id=current_user.id)
        except Exception:
            pass
    return {
        "id": item.id,
        "slug": item.slug,
        "title": item.title,
        "summary": item.summary,
        "status": item.status.value,
    }


@router.patch("/bulk", summary="Bulk node patch (admin, alias)")
async def bulk_node_operation_alias(
    payload: NodeBulkPatch,
    current_user=Depends(admin_required),  # noqa: B008
    db: Annotated[AsyncSession, Depends(get_db)] = ...,  # noqa: B008
):
    result = await db.execute(select(Node).where(Node.id.in_(payload.ids), Node.author_id == current_user.id))
    nodes = list(result.scalars().all())
    updated_ids: list[int] = []
    deleted_ids: list[int] = []
    cs = payload.changes
    for node in nodes:
        # Deletion takes precedence
        if getattr(cs, "delete", False):
            deleted_ids.append(node.id)
            await db.delete(node)
            continue
        changed = False
        if cs.is_visible is not None and node.is_visible != bool(cs.is_visible):
            node.is_visible = bool(cs.is_visible)
            changed = True
        if hasattr(node, "is_public") and cs.is_public is not None and node.is_public != bool(cs.is_public):
            node.is_public = bool(cs.is_public)
            changed = True
        if hasattr(node, "premium_only") and cs.premium_only is not None and node.premium_only != bool(cs.premium_only):
            node.premium_only = bool(cs.premium_only)
            changed = True
        if hasattr(node, "is_recommendable") and cs.is_recommendable is not None and node.is_recommendable != bool(cs.is_recommendable):
            node.is_recommendable = bool(cs.is_recommendable)
            changed = True
        if changed:
            try:
                from datetime import datetime as _dt

                node.updated_at = _dt.utcnow()
                node.updated_by_user_id = getattr(current_user, "id", None)
            except Exception:
                pass
            updated_ids.append(node.id)
            await navsvc.invalidate_navigation_cache(db, node)
    await db.commit()
    for _nid in updated_ids:
        try:
            await navcache.invalidate_navigation_by_user(current_user.id)
            await navcache.invalidate_compass_by_user(current_user.id)
        except Exception:
            pass
    return {"updated": updated_ids, "deleted": deleted_ids}


@router.delete("/{id}", summary="Delete node by ID (admin, alias)")
async def delete_node_admin_alias(
    id: int,
    current_user=Depends(admin_required),  # noqa: B008
    db: Annotated[AsyncSession, Depends(get_db)] = ...,  # noqa: B008
):
    repo = NodeRepository(db)
    node = await repo.get_by_id_simple(id)
    if not node or node.author_id != current_user.id:
        raise HTTPException(status_code=404, detail="Node not found")
    if not node:
        raise HTTPException(status_code=404, detail="Node not found")
    await db.delete(node)
    await db.commit()
    try:
        await navcache.invalidate_navigation_by_user(current_user.id)
        await navcache.invalidate_compass_by_user(current_user.id)
    except Exception:
        pass
    return {"deleted": True}


# Editor alias endpoints
class _PublishIn(BaseModel):
    access: Literal["everyone", "premium_only", "early_access"] = "everyone"
    cover: str | None = None
    scheduled_at: datetime | None = None


@router.get("/{node_id}", summary="Get node item by id (alias)")
async def get_node_item_alias(
    node_id: int,
    current_user=Depends(admin_required),  # noqa: B008
    db: Annotated[AsyncSession, Depends(get_db)] = ...,  # noqa: B008
):
    node_item = await _resolve_content_item_id(db, node_or_item_id=node_id)
    svc = NodeService(db)
    item = await svc.get(node_item.id)
    node = await db.scalar(select(Node).where(Node.id == item.node_id).options(selectinload(Node.tags)))
    return _serialize(item, node)


@router.patch("/{node_id}", summary="Update node item by id (alias)")
async def update_node_item_alias(
    node_id: int,
    payload: dict,
    next: int = 0,
    current_user: Annotated[User, Depends(auth_user)] = ...,  # noqa: B008
    db: Annotated[AsyncSession, Depends(get_db)] = ...,  # noqa: B008
):
    node_item = await _resolve_content_item_id(db, node_or_item_id=node_id)
    svc = NodeService(db)
    item = await svc.update_personal(node_item.id, payload, actor_id=current_user.id)
    if next:
        try:
            from app.domains.telemetry.application.ux_metrics_facade import ux_metrics

            ux_metrics.inc_save_next()
        except Exception:
            pass
    node = await db.scalar(select(Node).where(Node.id == item.node_id).options(selectinload(Node.tags)))
    return _serialize(item, node)


@router.post("/{node_id}/publish", summary="Publish node item by id (alias)")
async def publish_node_item_alias(
    node_id: int,
    payload: _PublishIn | None = None,
    current_user: Annotated[User, Depends(auth_user)] = ...,  # noqa: B008
    db: Annotated[AsyncSession, Depends(get_db)] = ...,  # noqa: B008
):
    node_item = await _resolve_content_item_id(db, node_or_item_id=node_id)
    svc = NodeService(db)
    item = await svc.publish_personal(
        node_item.id,
        actor_id=current_user.id,
        access=(payload.access if payload else "everyone"),
        scheduled_at=(payload.scheduled_at if payload else None),
    )
    from app.domains.nodes.service import publish_content

    await publish_content(node_id=item.id, slug=item.slug, author_id=current_user.id)
    node = await db.scalar(select(Node).where(Node.id == item.node_id))
    return _serialize(item, node)


@router.get("/{id}/publish_info", summary="Publish status and schedule (alias)")
async def get_publish_info_alias(
    id: int,
    current_user=Depends(admin_required),  # noqa: B008
    db: Annotated[AsyncSession, Depends(get_db)] = ...,  # noqa: B008
):
    item = await _resolve_content_item_id(db, node_or_item_id=id)
    res = await db.execute(select(NodePublishJob).where(NodePublishJob.node_id == id, NodePublishJob.status == "pending"))
    job = res.scalar_one_or_none()
    status = item.status.value if hasattr(item.status, "value") else str(item.status)
    payload: dict = {
        "status": status,
        "published_at": item.published_at.isoformat() if item.published_at else None,
        "scheduled": None,
    }
    if job:
        payload["scheduled"] = {
            "run_at": job.scheduled_at.isoformat(),
            "access": job.access,
            "status": job.status,
        }
    return payload


class _SchedulePublishIn(BaseModel):
    run_at: datetime
    access: Literal["everyone", "premium_only", "early_access"] = "everyone"


@router.post("/{id}/schedule_publish", summary="Schedule publish by date/time (alias)")
async def schedule_publish_alias(
    id: int,
    payload: _SchedulePublishIn,
    current_user=Depends(admin_required),  # noqa: B008
    db: Annotated[AsyncSession, Depends(get_db)] = ...,  # noqa: B008
):
    item = await _resolve_content_item_id(db, node_or_item_id=id)
    res = await db.execute(select(NodePublishJob).where(NodePublishJob.node_id == id, NodePublishJob.status == "pending"))
    existing = res.scalar_one_or_none()
    if existing:
        existing.status = "canceled"
    job = NodePublishJob(

        node_id=id,
        content_id=item.id,
        access=payload.access,
        scheduled_at=payload.run_at,
        status="pending",
        created_by_user_id=current_user.id,
    )
    db.add(job)
    await db.commit()
    return {
        "scheduled": {
            "run_at": job.scheduled_at.isoformat(),
            "access": job.access,
            "status": job.status,
        }
    }


@router.delete("/{id}/schedule_publish", summary="Cancel scheduled publish (alias)")
async def cancel_scheduled_publish_alias(
    id: int,
    current_user=Depends(admin_required),  # noqa: B008
    db: Annotated[AsyncSession, Depends(get_db)] = ...,  # noqa: B008
):
    res = await db.execute(select(NodePublishJob).where(NodePublishJob.node_id == id, NodePublishJob.status == "pending"))
    job = res.scalar_one_or_none()
    if not job:
        raise HTTPException(status_code=404, detail="Publish job not found")
    job.status = "canceled"
    await db.commit()
    return {"canceled": True}


@router.post("/{id}/versions/{version}/rollback", summary="Rollback node to version (alias)")
async def rollback_version_alias(
    id: int,
    version: int,
    current_user: Annotated[User, Depends(auth_user)] = ...,  # noqa: B008
    db: Annotated[AsyncSession, Depends(get_db)] = ...,  # noqa: B008
):
    repo = NodeRepository(db)
    node = await repo.get_by_id_simple(id)
    if not node or node.author_id != current_user.id:
        raise HTTPException(status_code=404, detail="Node not found")
    node = await repo.rollback(node, version, current_user.id)
    return NodeOut.model_validate(node)


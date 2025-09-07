from __future__ import annotations

import time as _t
from datetime import datetime
from typing import Annotated, Literal, TypedDict
from uuid import UUID

from fastapi import (
    APIRouter,
    Body,
    Depends,
    Header,
    HTTPException,
    Path,
    Query,
    Request,
    Response,
)
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

from app.core.log_events import cache_invalidate
from app.domains.audit.application.audit_service import audit_log
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
from app.domains.nodes.content_admin_router import _resolve_content_item_id
from app.domains.nodes.content_admin_router import (
    get_node_by_id as _content_get_node_by_id,
)
from app.domains.nodes.content_admin_router import (
    publish_node_by_id as _content_publish_node_by_id,
)
from app.domains.nodes.content_admin_router import (
    update_node_by_id as _content_update_node_by_id,
)
from app.domains.nodes.infrastructure.models.node import Node
from app.domains.nodes.infrastructure.repositories.node_repository import (
    NodeRepository,
)
from app.domains.nodes.models import NodeItem, NodePublishJob
from app.domains.nodes.schemas.node import NodeBulkOperation, NodeBulkPatch, NodeOut
from app.providers.db.session import get_db
from app.schemas.nodes_common import Status
from app.schemas.workspaces import WorkspaceType
from app.security import ADMIN_AUTH_RESPONSES, require_admin_role

router = APIRouter(
    prefix="/admin/accounts/{account_id}/nodes",
    tags=["admin"],
    responses=ADMIN_AUTH_RESPONSES,
)
admin_required = require_admin_role()

navcache = NavigationCacheService(CoreCacheAdapter())
navsvc = NavigationService()


def _serialize(item: NodeItem) -> dict:
    return {
        "id": item.id,
        "workspace_id": str(item.workspace_id),
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
    limit: int
    offset: int
    date_from: datetime
    date_to: datetime
    q: str
    status: Status


@router.get("", response_model=list[NodeOut], summary="List nodes (admin)")
async def list_nodes_admin(
    response: Response,
    account_id: Annotated[int, Path(...)],  # noqa: B008 - accounts are integers
    if_none_match: Annotated[str | None, Header(alias="If-None-Match")] = None,
    author: UUID | None = None,
    sort: Annotated[
        Literal[
            "updated_desc",
            "created_desc",
            "created_asc",
            "views_desc",
        ],
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
    """List nodes in workspace.

    See :class:`AdminNodeListParams` for available query parameters.
    """
    if scope_mode is None:
        scope_mode = "member"
    # In profile-first mode, account_id acts as a workspace filter. Global scope ignores it.
    filter_account_id: int | None = None if scope_mode == "global" else int(account_id)
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
    t0 = _t.perf_counter()
    etag = await svc.compute_nodes_etag(spec, ctx, page, account_id=filter_account_id)
    t_etag = _t.perf_counter()
    nodes = await svc.list_nodes(spec, page, ctx, account_id=filter_account_id)
    t_list = _t.perf_counter()
    try:
        response.headers["ETag"] = etag
    except Exception:
        pass
    try:
        # Lightweight server-side timing to quickly spot DB vs. app overhead
        import logging as _logging

        _logging.getLogger(__name__).info(
            "admin.nodes_list_timing",
            extra={
                "account_id": str(account_id),
                "compute_etag_ms": int((t_etag - t0) * 1000),
                "list_nodes_ms": int((t_list - t_etag) * 1000),
                "total_ms": int((t_list - t0) * 1000),
                "limit": int(limit or 0),
                "offset": int(offset or 0),
            },
        )
    except Exception:
        pass
    return nodes


@router.post("", summary="Create node (admin)")
async def create_node_admin(
    account_id: Annotated[UUID, Path(...)],  # noqa: B008
    payload: dict | None = Body(  # noqa: B008
        default=None,
        example={
            "title": "New quest",
            "content": {"time": 0, "blocks": [], "version": "2.30.7"},
            "tags": ["intro"],
            "media": ["https://example.com/image.png"],
        },
    ),
    current_user=Depends(admin_required),  # noqa: B008
    db: Annotated[AsyncSession, Depends(get_db)] = ...,  # noqa: B008
):
    svc = NodeService(db)
    item = await svc.create(account_id, actor_id=current_user.id)
    # Если в теле пришёл title/slug/content и т.п. — применим сразу же
    if payload:
        try:
            item = await svc.update(
                account_id,
                item.id,
                payload,
                actor_id=current_user.id,
            )
        except Exception:
            # не валим создание, если патч не применился; вернём базовый item
            pass
    return _serialize(item)


@router.post("/bulk", summary="Bulk node operations")
async def bulk_node_operation(
    payload: NodeBulkOperation,
    account_id: Annotated[UUID, Path(...)],  # noqa: B008
    current_user=Depends(admin_required),  # noqa: B008
    db: Annotated[AsyncSession, Depends(get_db)] = ...,  # noqa: B008
):
    result = await db.execute(
        select(Node)
        .join(NodeItem, NodeItem.node_id == Node.id)
        .where(Node.id.in_(payload.ids), NodeItem.workspace_id == account_id)
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
        await navcache.invalidate_navigation_by_node(account_id=account_id, node_slug=slug)
        await navcache.invalidate_modes_by_node(account_id=account_id, node_slug=slug)
        cache_invalidate("nav", reason="node_bulk", key=slug)
        cache_invalidate("navm", reason="node_bulk", key=slug)
    if invalidate_slugs:
        await navcache.invalidate_compass_all()
        cache_invalidate("comp", reason="node_bulk")
    return {"updated": [n.id for n in nodes]}


@router.patch("/bulk", summary="Bulk update nodes")
async def bulk_patch_nodes(
    payload: NodeBulkPatch,
    account_id: Annotated[UUID, Path(...)],  # noqa: B008
    current_user=Depends(admin_required),  # noqa: B008
    db: Annotated[AsyncSession, Depends(get_db)] = ...,  # noqa: B008
):
    result = await db.execute(
        select(Node)
        .join(NodeItem, NodeItem.node_id == Node.id)
        .where(Node.id.in_(payload.ids), NodeItem.workspace_id == account_id)
    )
    nodes = result.scalars().all()
    updated_ids: list[int] = []
    deleted_ids: list[int] = []
    invalidate_slugs: list[str] = []
    for node in nodes:
        changes = payload.changes
        if changes.delete:
            invalidate_slugs.append(node.slug)
            deleted_ids.append(node.id)
            try:
                await navsvc.invalidate_navigation_cache(db, node)
            except Exception:
                pass
            await db.delete(node)
            continue
        was_visible = node.is_visible
        was_public = node.is_public
        if changes.is_visible is not None:
            node.is_visible = changes.is_visible
        if changes.is_public is not None:
            node.is_public = changes.is_public
        if changes.premium_only is not None:
            node.premium_only = changes.premium_only
        if changes.is_recommendable is not None:
            node.is_recommendable = changes.is_recommendable
        if changes.account_id is not None:
            node.account_id = changes.account_id
        node.updated_at = datetime.utcnow()
        node.updated_by_user_id = current_user.id
        updated_ids.append(node.id)
        if (
            (changes.is_visible is not None and changes.is_visible != was_visible)
            or (changes.is_public is not None and changes.is_public != was_public)
            or changes.account_id is not None
        ):
            invalidate_slugs.append(node.slug)
            try:
                await navsvc.invalidate_navigation_cache(db, node)
            except Exception:
                pass
    await db.commit()
    for slug in invalidate_slugs:
        await navcache.invalidate_navigation_by_node(account_id=account_id, node_slug=slug)
        await navcache.invalidate_modes_by_node(account_id=account_id, node_slug=slug)
        cache_invalidate("nav", reason="node_bulk_patch", key=slug)
        cache_invalidate("navm", reason="node_bulk_patch", key=slug)
    if invalidate_slugs:
        await navcache.invalidate_compass_all()
        cache_invalidate("comp", reason="node_bulk_patch")
    return {"updated": updated_ids, "deleted": deleted_ids}


@router.get("/{id}", summary="Get node by ID (admin, full)")
async def get_node_by_id_admin(
    account_id: Annotated[UUID, Path(...)],  # noqa: B008
    id: Annotated[int, Path(...)],  # noqa: B008
    current_user=Depends(admin_required),  # noqa: B008
    db: Annotated[AsyncSession, Depends(get_db)] = ...,  # noqa: B008
):
    """
    Единая точка для загрузки полной ноды по ID (числовой node.id).
    Делегирует обработку в контент‑роутер, который самостоятельно
    резолвит идентификатор контента.
    """
    return await _content_get_node_by_id(node_id=id, account_id=account_id, db=db)


@router.patch("/{id}", summary="Update node by ID (admin, full)")
async def update_node_by_id_admin(
    account_id: Annotated[UUID, Path(...)],  # noqa: B008
    id: Annotated[int, Path(...)],  # noqa: B008
    payload: dict = Body(  # noqa: B008
        example={
            "title": "Updated quest",
            "content": {"time": 0, "blocks": [], "version": "2.30.7"},
            "tags": ["intro"],
            "media": ["https://example.com/image.png"],
        }
    ),
    current_user=Depends(admin_required),  # noqa: B008
    db: Annotated[AsyncSession, Depends(get_db)] = ...,  # noqa: B008
):
    """
    Обновление полной ноды по числовому ID с возвратом полного объекта.
    Делегируем в контент‑роутер, который резолвит идентификатор контента.
    """
    return await _content_update_node_by_id(
        node_id=id,
        payload=payload,
        account_id=account_id,
        current_user=current_user,
        db=db,
    )


@router.post("/{id}/publish", summary="Publish node by ID (admin)")
async def publish_node_by_id_admin(
    account_id: Annotated[UUID, Path(...)],  # noqa: B008
    id: Annotated[int, Path(...)],  # noqa: B008
    payload: dict | None = None,
    current_user=Depends(admin_required),  # noqa: B008
    db: Annotated[AsyncSession, Depends(get_db)] = ...,  # noqa: B008
):
    """
    Публикация ноды по числовому ID. Возвращает обновлённую полную ноду.
    Делегируем в контент‑роутер, который резолвит идентификатор контента.
    """
    return await _content_publish_node_by_id(
        node_id=id,
        account_id=account_id,
        payload=payload or {},
        current_user=current_user,
        db=db,
    )


class SchedulePublishIn(BaseModel):
    run_at: datetime
    access: Literal["everyone", "premium_only", "early_access"] = "everyone"


@router.get("/{id}/publish_info", summary="Publish status and schedule (admin)")
async def get_publish_info(
    account_id: Annotated[UUID, Path(...)],  # noqa: B008
    id: Annotated[int, Path(...)],  # noqa: B008
    current_user=Depends(admin_required),  # noqa: B008
    db: Annotated[AsyncSession, Depends(get_db)] = ...,  # noqa: B008
):
    """Возвращает статус публикации и запланированную публикацию."""
    item = await _resolve_content_item_id(db, account_id=account_id, node_or_item_id=id)
    if item.workspace_id != account_id:
        raise HTTPException(status_code=404, detail="Node not found")

    res = await db.execute(
        select(NodePublishJob).where(
            NodePublishJob.workspace_id == account_id,
            NodePublishJob.node_id == id,
            NodePublishJob.status == "pending",
        )
    )
    job = res.scalar_one_or_none()

    status = item.status.value if hasattr(item.status, "value") else str(item.status)
    payload = {
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


@router.post("/{id}/schedule_publish", summary="Schedule publish by date/time (admin)")
async def schedule_publish(
    payload: SchedulePublishIn,
    account_id: Annotated[UUID, Path(...)],  # noqa: B008
    id: Annotated[int, Path(...)],  # noqa: B008
    current_user=Depends(admin_required),  # noqa: B008
    db: Annotated[AsyncSession, Depends(get_db)] = ...,  # noqa: B008,
):
    """Создаёт или заменяет задание на публикацию."""
    item = await _resolve_content_item_id(db, account_id=account_id, node_or_item_id=id)

    res = await db.execute(
        select(NodePublishJob).where(
            NodePublishJob.workspace_id == account_id,
            NodePublishJob.node_id == id,
            NodePublishJob.status == "pending",
        )
    )
    existing = res.scalar_one_or_none()
    if existing:
        existing.status = "canceled"

    job = NodePublishJob(
        workspace_id=account_id,
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


@router.delete("/{id}/schedule_publish", summary="Cancel scheduled publish (admin)")
async def cancel_scheduled_publish(
    account_id: Annotated[UUID, Path(...)],  # noqa: B008
    id: Annotated[int, Path(...)],  # noqa: B008
    current_user=Depends(admin_required),  # noqa: B008
    db: Annotated[AsyncSession, Depends(get_db)] = ...,  # noqa: B008,
):
    res = await db.execute(
        select(NodePublishJob).where(
            NodePublishJob.workspace_id == account_id,
            NodePublishJob.node_id == id,
            NodePublishJob.status == "pending",
        )
    )
    job = res.scalar_one_or_none()
    if not job:
        raise HTTPException(status_code=404, detail="Publish job not found")
    job.status = "canceled"
    await db.commit()
    return {"canceled": True}


@router.post("/{id}/versions/{version}/rollback", summary="Rollback node to version")
async def rollback_version(
    account_id: Annotated[UUID, Path(...)],  # noqa: B008
    id: Annotated[int, Path(...)],  # noqa: B008
    version: Annotated[int, Path(...)],  # noqa: B008
    request: Request,
    current_user=Depends(admin_required),  # noqa: B008
    db: Annotated[AsyncSession, Depends(get_db)] = ...,  # noqa: B008
):
    repo = NodeRepository(db)
    node = await repo.get_by_id(id, account_id.int)
    if not node:
        raise HTTPException(status_code=404, detail="Node not found")
    node = await repo.rollback(node, version, current_user.id)
    await audit_log(
        db,
        actor_id=str(current_user.id),
        action="node_version_rollback",
        resource_type="node",
        resource_id=str(id),
        after={"to_version": version},
        request=request,
        workspace_id=str(account_id),
    )
    return NodeOut.model_validate(node)

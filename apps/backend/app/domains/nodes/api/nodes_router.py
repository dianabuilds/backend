# ruff: noqa
from __future__ import annotations

from typing import List, Literal, TypedDict, Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, Header, HTTPException, Query, Request, Response
from fastapi.responses import RedirectResponse
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import (
    ensure_can_post,
    get_current_user,
    require_premium,
)
from app.core.db.session import get_db
from app.core.log_events import cache_invalidate
from app.core.workspace_context import optional_workspace, require_workspace
from app.domains.navigation.application.navigation_cache_service import (
    NavigationCacheService,
)
from app.domains.navigation.application.navigation_service import NavigationService
from app.domains.navigation.application.traces_service import TracesService
from app.domains.navigation.infrastructure.cache_adapter import CoreCacheAdapter
from app.domains.nodes.application.query_models import (
    NodeFilterSpec,
    PageRequest,
    QueryContext,
)
from app.domains.nodes.infrastructure.queries.node_query_adapter import NodeQueryAdapter
from app.domains.nodes.infrastructure.repositories.node_repository import (
    NodeRepositoryAdapter as NodeRepository,
)
from app.domains.nodes.models import NodeItem
from app.domains.nodes.policies.node_policy import NodePolicy
from app.domains.nodes.schemas.feedback import FeedbackCreate, FeedbackOut
from app.domains.nodes.schemas.node import (
    NodeCreate,
    NodeOut,
    NodeUpdate,
)
from app.domains.notifications.infrastructure.repositories.settings_repository import (
    NodeNotificationSettingsRepository,
)
from app.domains.system.events import NodeCreated, NodeUpdated, get_event_bus
from app.domains.telemetry.application.event_metrics_facade import event_metrics
from app.domains.users.infrastructure.models.user import User
from app.domains.users.nft import user_has_nft
from app.schemas.notification_settings import (
    NodeNotificationSettingsOut,
    NodeNotificationSettingsUpdate,
)
from app.security import require_ws_guest, require_ws_viewer
from app.schemas.nodes_common import Status
from app.core.feature_flags import get_effective_flags

router = APIRouter(prefix="/nodes", tags=["nodes"])
navcache = NavigationCacheService(CoreCacheAdapter())
navsvc = NavigationService()


class NodeListParams(TypedDict, total=False):
    sort: Literal[
        "updated_desc",
        "created_desc",
        "created_asc",
        "views_desc",
    ]


def _ensure_workspace_id(request: Request, workspace_id: UUID | None) -> UUID:
    if workspace_id is not None:
        return workspace_id
    wid = getattr(request.state, "workspace_id", None)
    if wid is None:
        raise HTTPException(status_code=400, detail="workspace_id is required")
    return UUID(str(wid))


@router.get("", response_model=List[NodeOut], summary="List nodes")
async def list_nodes(
    request: Request,
    response: Response,
    workspace_id: UUID | None = None,
    if_none_match: Annotated[str | None, Header(alias="If-None-Match")] = None,
    sort: Annotated[
        Literal[
            "updated_desc",
            "created_desc",
            "created_asc",
            "views_desc",
        ],
        Query(),
    ] = "updated_desc",
    current_user: Annotated[User, Depends(get_current_user)] = ...,
    db: Annotated[AsyncSession, Depends(get_db)] = ...,
    workspace_dep: Annotated[object, Depends(optional_workspace)] = ...,
    _: Annotated[object, Depends(require_ws_guest)] = ...,
) -> List[NodeOut]:
    """List nodes.

    See :class:`NodeListParams` for available query parameters.
    """
    workspace_id = _ensure_workspace_id(request, workspace_id)
    spec = NodeFilterSpec(workspace_id=workspace_id, sort=sort)
    ctx = QueryContext(user=current_user, is_admin=False)
    service = NodeQueryAdapter(db)
    page = PageRequest()
    etag = await service.compute_nodes_etag(spec, ctx, page)
    if if_none_match and if_none_match == etag:
        response.headers["ETag"] = etag
        # 304 Not Modified
        raise HTTPException(status_code=304, detail="Not Modified")
    nodes = await service.list_nodes(spec, page, ctx)
    response.headers["ETag"] = etag
    return nodes


@router.post("", response_model=dict, summary="Create node")
async def create_node(
    request: Request,
    payload: NodeCreate,
    workspace_id: UUID | None = None,
    current_user: Annotated[User, Depends(ensure_can_post)] = ...,
    db: Annotated[AsyncSession, Depends(get_db)] = ...,
    _workspace: Annotated[object, Depends(require_workspace)] = ...,
):
    workspace_id = _ensure_workspace_id(request, workspace_id)
    await require_ws_viewer(workspace_id=workspace_id, user=current_user, db=db)
    repo = NodeRepository(db)
    node = await repo.create(payload, current_user.id, workspace_id)
    await get_event_bus().publish(
        NodeCreated(node_id=node.id, slug=node.slug, author_id=current_user.id)
    )
    return {"slug": node.slug}


@router.get("/{slug}", response_model=NodeOut, summary="Get node")
async def read_node(
    request: Request,
    slug: str,
    workspace_id: UUID | None = None,
    current_user: Annotated[User, Depends(get_current_user)] = ...,
    db: Annotated[AsyncSession, Depends(get_db)] = ...,
    workspace_dep: Annotated[object, Depends(optional_workspace)] = ...,
):
    if workspace_id is None:
        wid = getattr(request.state, "workspace_id", None)
        if wid is not None:
            workspace_id = UUID(str(wid))
    repo = NodeRepository(db)
    if workspace_id is not None:
        node = await repo.get_by_slug(slug, workspace_id)
    else:
        node = await repo.get_by_slug(slug)
    if not node:
        raise HTTPException(status_code=404, detail="Node not found")
    if workspace_id is None:
        workspace_id = node.workspace_id
    if workspace_id is None:
        raise HTTPException(status_code=400, detail="workspace_id is required")
    request.state.workspace_id = str(workspace_id)
    await require_ws_guest(workspace_id=workspace_id, user=current_user, db=db)
    res = await db.execute(
        select(NodeItem)
        .where(
            NodeItem.node_id == node.id,
            NodeItem.status == Status.published,
        )
        .order_by(NodeItem.version.desc())
        .limit(1)
    )
    item = res.scalar_one_or_none()
    if item and item.type == "quest":
        flags = await get_effective_flags(db, request.headers.get("X-Preview-Flags"))
        if "quests.nodes_redirect" in flags:
            return RedirectResponse(
                url=f"/quests/{node.id}/versions/current?workspace_id={workspace_id}",
                status_code=307,
            )
    NodePolicy.ensure_can_view(node, current_user)
    if node.premium_only:
        await require_premium(current_user)
    if node.nft_required and not await user_has_nft(current_user, node.nft_required):
        raise HTTPException(status_code=403, detail="NFT required")
    node = await repo.increment_views(node)
    event_metrics.inc("node_visit", str(workspace_id))
    await TracesService().maybe_add_auto_trace(db, node, current_user)
    return node


@router.patch("/{slug}", response_model=NodeOut, summary="Update node")
async def update_node(
    request: Request,
    slug: str,
    payload: NodeUpdate,
    workspace_id: UUID | None = None,
    current_user: Annotated[User, Depends(get_current_user)] = ...,
    db: Annotated[AsyncSession, Depends(get_db)] = ...,
    _workspace: Annotated[object, Depends(require_workspace)] = ...,
    _: Annotated[object, Depends(require_ws_viewer)] = ...,
):
    workspace_id = _ensure_workspace_id(request, workspace_id)
    repo = NodeRepository(db)
    node = await repo.get_by_slug(slug, workspace_id)
    if not node:
        raise HTTPException(status_code=404, detail="Node not found")
    NodePolicy.ensure_can_edit(node, current_user)
    was_visible = node.is_visible
    node = await repo.update(node, payload, current_user.id)
    if was_visible != node.is_visible:
        await navsvc.invalidate_navigation_cache(db, node)
        await navcache.invalidate_navigation_by_node(slug)
        await navcache.invalidate_modes_by_node(slug)
        await navcache.invalidate_compass_all()
        cache_invalidate("nav", reason="node_update", key=slug)
        cache_invalidate("navm", reason="node_update", key=slug)
        cache_invalidate("comp", reason="node_update")
    await get_event_bus().publish(
        NodeUpdated(
            node_id=node.id,
            slug=node.slug,
            author_id=current_user.id,
        )
    )
    return node


@router.delete("/{slug}", summary="Delete node")
async def delete_node(
    request: Request,
    slug: str,
    workspace_id: UUID | None = None,
    current_user: Annotated[User, Depends(get_current_user)] = ...,
    db: Annotated[AsyncSession, Depends(get_db)] = ...,
    _workspace: Annotated[object, Depends(require_workspace)] = ...,
    _: Annotated[object, Depends(require_ws_viewer)] = ...,
):
    workspace_id = _ensure_workspace_id(request, workspace_id)
    repo = NodeRepository(db)
    node = await repo.get_by_slug(slug, workspace_id)
    if not node:
        raise HTTPException(status_code=404, detail="Node not found")
    NodePolicy.ensure_can_edit(node, current_user)
    await repo.delete(node)
    await navsvc.invalidate_navigation_cache(db, node)
    await navcache.invalidate_navigation_by_node(slug)
    await navcache.invalidate_modes_by_node(slug)
    await navcache.invalidate_compass_all()
    cache_invalidate("nav", reason="node_delete", key=slug)
    cache_invalidate("navm", reason="node_delete", key=slug)
    cache_invalidate("comp", reason="node_delete")
    return {"message": "Node deleted"}


@router.get(
    "/{node_id}/notification-settings",
    response_model=NodeNotificationSettingsOut,
    summary="Get node notification settings",
)
async def get_node_notification_settings(
    request: Request,
    node_id: int,
    workspace_id: UUID | None = None,
    current_user: Annotated[User, Depends(get_current_user)] = ...,
    db: Annotated[AsyncSession, Depends(get_db)] = ...,
    workspace_dep: Annotated[object, Depends(optional_workspace)] = ...,
    _: Annotated[object, Depends(require_ws_viewer)] = ...,
) -> NodeNotificationSettingsOut:
    workspace_id = _ensure_workspace_id(request, workspace_id)
    repo = NodeRepository(db)
    node = await repo.get_by_id(node_id, workspace_id)
    if not node:
        raise HTTPException(status_code=404, detail="Node not found")
    settings_repo = NodeNotificationSettingsRepository(db)
    setting = await settings_repo.get(current_user.id, node.id)
    if not setting:
        return NodeNotificationSettingsOut(node_id=node.id, enabled=True)
    return NodeNotificationSettingsOut.model_validate(setting)


@router.patch(
    "/{node_id}/notification-settings",
    response_model=NodeNotificationSettingsOut,
    summary="Update node notification settings",
)
async def update_node_notification_settings(
    request: Request,
    node_id: int,
    payload: NodeNotificationSettingsUpdate,
    workspace_id: UUID | None = None,
    current_user: Annotated[User, Depends(get_current_user)] = ...,
    db: Annotated[AsyncSession, Depends(get_db)] = ...,
    _workspace: Annotated[object, Depends(require_workspace)] = ...,
    _: Annotated[object, Depends(require_ws_viewer)] = ...,
) -> NodeNotificationSettingsOut:
    workspace_id = _ensure_workspace_id(request, workspace_id)
    repo = NodeRepository(db)
    node = await repo.get_by_id(node_id, workspace_id)
    if not node:
        raise HTTPException(status_code=404, detail="Node not found")
    settings_repo = NodeNotificationSettingsRepository(db)
    setting = await settings_repo.upsert(current_user.id, node.id, payload.enabled)
    return NodeNotificationSettingsOut.model_validate(setting)


@router.get(
    "/{slug}/feedback", response_model=List[FeedbackOut], summary="List feedback"
)
async def list_feedback(
    request: Request,
    slug: str,
    workspace_id: UUID | None = None,
    current_user: Annotated[User, Depends(get_current_user)] = ...,
    db: Annotated[AsyncSession, Depends(get_db)] = ...,
    workspace_dep: Annotated[object, Depends(optional_workspace)] = ...,
    _: Annotated[object, Depends(require_ws_viewer)] = ...,
):
    from app.domains.nodes.application.feedback_service import FeedbackService
    from app.domains.nodes.infrastructure.repositories.node_repository import (
        NodeRepositoryAdapter,
    )

    workspace_id = _ensure_workspace_id(request, workspace_id)
    service = FeedbackService(NodeRepositoryAdapter(db))
    return await service.list_feedback(db, slug, current_user, workspace_id)


@router.post("/{slug}/feedback", response_model=FeedbackOut, summary="Create feedback")
async def create_feedback(
    request: Request,
    slug: str,
    payload: FeedbackCreate,
    workspace_id: UUID | None = None,
    current_user: Annotated[User, Depends(get_current_user)] = ...,
    db: Annotated[AsyncSession, Depends(get_db)] = ...,
    _workspace: Annotated[object, Depends(require_workspace)] = ...,
    _: Annotated[object, Depends(require_ws_viewer)] = ...,
):
    from app.domains.nodes.application.feedback_service import FeedbackService
    from app.domains.nodes.infrastructure.repositories.node_repository import (
        NodeRepositoryAdapter,
    )
    from app.domains.notifications.application.notify_service import NotifyService
    from app.domains.notifications.infrastructure.repositories.notification_repository import (
        NotificationRepository,
    )
    from app.domains.notifications.infrastructure.transports.websocket import (
        WebsocketPusher,
    )
    from app.domains.notifications.infrastructure.transports.websocket import (
        manager as ws_manager,
    )

    notifier = NotifyService(NotificationRepository(db), WebsocketPusher(ws_manager))
    workspace_id = _ensure_workspace_id(request, workspace_id)
    service = FeedbackService(NodeRepositoryAdapter(db), notifier)
    return await service.create_feedback(
        db, slug, payload.content, payload.is_anonymous, current_user, workspace_id
    )


@router.delete(
    "/{slug}/feedback/{feedback_id}", response_model=dict, summary="Delete feedback"
)
async def delete_feedback(
    request: Request,
    slug: str,
    feedback_id: UUID,
    workspace_id: UUID | None = None,
    current_user: Annotated[User, Depends(get_current_user)] = ...,
    db: Annotated[AsyncSession, Depends(get_db)] = ...,
    _workspace: Annotated[object, Depends(require_workspace)] = ...,
    _: Annotated[object, Depends(require_ws_viewer)] = ...,
):
    from app.domains.nodes.application.feedback_service import FeedbackService
    from app.domains.nodes.infrastructure.repositories.node_repository import (
        NodeRepositoryAdapter,
    )

    workspace_id = _ensure_workspace_id(request, workspace_id)
    service = FeedbackService(NodeRepositoryAdapter(db))
    return await service.delete_feedback(
        db, slug, feedback_id, current_user, workspace_id
    )

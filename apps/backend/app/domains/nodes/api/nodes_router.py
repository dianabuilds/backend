# ruff: noqa
from __future__ import annotations

from typing import List, Literal, TypedDict, Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, Header, HTTPException, Query, Request, Response
from starlette.background import BackgroundTask
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import (
    ensure_can_post,
    get_current_user,
    require_premium,
)
from app.providers.db.session import get_db
from app.core.log_events import cache_invalidate
from app.domains.navigation.application.navigation_cache_service import (
    NavigationCacheService,
)
from app.domains.navigation.application.navigation_service import NavigationService
from app.domains.navigation.application.traces_service import TracesService
from app.domains.navigation.infrastructure.cache_adapter import CoreCacheAdapter
from app.domains.audit.application.audit_service import audit_log
from app.domains.nodes.application.query_models import (
    NodeFilterSpec,
    PageRequest,
    QueryContext,
)
from app.domains.nodes.application.node_query_service import NodeQueryService
from app.domains.nodes.infrastructure.repositories.node_repository import (
    NodeRepository,
)
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
from app.domains.users.application.nft_service import user_has_nft
from app.schemas.notification_settings import (
    NodeNotificationSettingsOut,
    NodeNotificationSettingsUpdate,
)
from app.security import require_admin_role

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


# Profile-only mode: no cross-tenant resolution


@router.get("", response_model=List[NodeOut], summary="List nodes")
async def list_nodes(
    request: Request,
    response: Response,
    scope_mode: Annotated[
        str | None,
        Query(
            regex="^(mine|member|invited|space:[0-9]+|global)$",
            description="Listing scope mode",
        ),
    ] = None,
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
) -> List[NodeOut]:
    """List nodes.

    See :class:`NodeListParams` for available query parameters.
    """
    # Profile-first logic: default to personal scope
    if scope_mode is None:
        scope_mode = "mine"

    spec = NodeFilterSpec(sort=sort)
    ctx = QueryContext(user=current_user, is_admin=False)
    service = NodeQueryService(db)
    page = PageRequest()
    etag = await service.compute_nodes_etag(spec, ctx, page, scope_mode=scope_mode)
    if if_none_match and if_none_match == etag:
        response.headers["ETag"] = etag
        # 304 Not Modified
        raise HTTPException(status_code=304, detail="Not Modified")
    nodes = await service.list_nodes(spec, page, ctx, scope_mode=scope_mode)
    response.headers["ETag"] = etag
    return nodes


@router.post("", response_model=dict, summary="Create node")
async def create_node(
    request: Request,
    payload: NodeCreate,
    current_user: Annotated[User, Depends(ensure_can_post)] = ...,
    db: Annotated[AsyncSession, Depends(get_db)] = ...,
):
    repo = NodeRepository(db)
    node = await repo.create_personal(payload, current_user.id)
    await get_event_bus().publish(
        NodeCreated(node_id=node.id, slug=node.slug, author_id=current_user.id)
    )
    return {"slug": node.slug}


@router.get("/{slug}", response_model=NodeOut, summary="Get node")
async def read_node(
    request: Request,
    slug: str,
    response: Response,
    _feature_flags: Annotated[str | None, Header(alias="X-Feature-Flags")] = None,
    preview_version: Annotated[int | None, Header(alias="X-Preview-Version")] = None,
    current_user: Annotated[User, Depends(get_current_user)] = ...,
    db: Annotated[AsyncSession, Depends(get_db)] = ...,
):
    repo = NodeRepository(db)
    node = await repo.get_by_slug_for_author(slug, current_user.id)
    if not node:
        raise HTTPException(status_code=404, detail="Node not found")
    override = bool(getattr(request.state, "admin_override", False))
    NodePolicy.ensure_can_view(node, current_user, override=override)
    if node.premium_only:
        await require_premium(current_user)
    if node.nft_required and not await user_has_nft(current_user, node.nft_required):
        raise HTTPException(status_code=403, detail="NFT required")
    if preview_version:
        version = await repo.get_version(node.id, int(preview_version))
        if version:
            out = NodeOut.model_validate(node)
            out.title = version.title
            out.meta = version.meta or {}
            return out
    node.views = int(node.views or 0) + 1
    await db.flush()
    event_metrics.inc("node_visit", str(current_user.id))
    await TracesService().maybe_add_auto_trace(db, node, current_user)
    response.background = BackgroundTask(db.commit)
    return node


@router.patch("/{slug}", response_model=NodeOut, summary="Update node")
async def update_node(
    request: Request,
    slug: str,
    payload: NodeUpdate,
    current_user: Annotated[User, Depends(get_current_user)] = ...,
    db: Annotated[AsyncSession, Depends(get_db)] = ...,
):
    repo = NodeRepository(db)
    node = await repo.get_by_slug_for_author(slug, current_user.id)
    if not node:
        raise HTTPException(status_code=404, detail="Node not found")
    override = bool(getattr(request.state, "admin_override", False))
    NodePolicy.ensure_can_edit(node, current_user, override=override)
    before_snapshot = NodeOut.model_validate(node).model_dump()
    was_visible = node.is_visible
    node = await repo.update(node, payload, current_user.id)
    if override:
        after_snapshot = NodeOut.model_validate(node).model_dump()
        await audit_log(
            db,
            actor_id=str(current_user.id),
            action="node_update",
            resource_type="node",
            resource_id=str(node.id),
            before=before_snapshot,
            after=after_snapshot,
            request=request,
            reason=getattr(request.state, "override_reason", None),
            override=True,
        )
    if was_visible != node.is_visible:
        await navsvc.invalidate_navigation_cache(db, node)
        await navcache.invalidate_navigation_by_user(current_user.id)
        await navcache.invalidate_compass_by_user(current_user.id)
        cache_invalidate("nav", reason="node_update", key=slug)
        cache_invalidate("navm", reason="node_update", key=slug)
        cache_invalidate("comp", reason="node_update")
    await get_event_bus().publish(
        NodeUpdated(node_id=node.id, slug=node.slug, author_id=current_user.id)
    )
    return node


@router.delete("/{slug}", summary="Delete node")
async def delete_node(
    request: Request,
    slug: str,
    current_user: Annotated[User, Depends(get_current_user)] = ...,
    db: Annotated[AsyncSession, Depends(get_db)] = ...,
):
    repo = NodeRepository(db)
    node = await repo.get_by_slug_for_author(slug, current_user.id)
    if not node:
        raise HTTPException(status_code=404, detail="Node not found")
    override = bool(getattr(request.state, "admin_override", False))
    NodePolicy.ensure_can_edit(node, current_user, override=override)
    before_snapshot = NodeOut.model_validate(node).model_dump()
    await repo.delete(node)
    if override:
        await audit_log(
            db,
            actor_id=str(current_user.id),
            action="node_delete",
            resource_type="node",
            resource_id=str(node.id),
            before=before_snapshot,
            after=None,
            request=request,
            reason=getattr(request.state, "override_reason", None),
            override=True,
        )
    await navsvc.invalidate_navigation_cache(db, node)
    await navcache.invalidate_navigation_by_user(current_user.id)
    await navcache.invalidate_compass_by_user(current_user.id)
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
    current_user: Annotated[User, Depends(get_current_user)] = ...,
    db: Annotated[AsyncSession, Depends(get_db)] = ...,
) -> NodeNotificationSettingsOut:
    """Return notification settings without account dependency.

    Behavior:
    - Resolves the node globally and verifies authorship by the current user.
    - Does not require account membership checks.
    """
    repo = NodeRepository(db)
    node = await repo.get_by_id_simple(node_id)
    if not node or node.author_id != current_user.id:
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
    current_user: Annotated[User, Depends(get_current_user)] = ...,
    db: Annotated[AsyncSession, Depends(get_db)] = ...,
) -> NodeNotificationSettingsOut:
    """Update notification settings without account dependency.

    Only the author of the node may update their own notification settings.
    """
    repo = NodeRepository(db)
    node = await repo.get_by_id_simple(node_id)
    if not node or node.author_id != current_user.id:
        raise HTTPException(status_code=404, detail="Node not found")
    settings_repo = NodeNotificationSettingsRepository(db)
    setting = await settings_repo.upsert(current_user.id, node.id, payload.enabled)
    return NodeNotificationSettingsOut.model_validate(setting)


@router.get("/{slug}/feedback", response_model=List[FeedbackOut], summary="List feedback")
async def list_feedback(
    request: Request,
    slug: str,
    current_user: Annotated[User, Depends(get_current_user)] = ...,
    db: Annotated[AsyncSession, Depends(get_db)] = ...,
):
    from app.domains.nodes.application.feedback_service import FeedbackService
    from app.domains.nodes.infrastructure.repositories.node_repository import (
        NodeRepository,
    )

    service = FeedbackService(NodeRepository(db))
    return await service.list_feedback(db, slug, current_user, author_id=current_user.id)


@router.post("/{slug}/feedback", response_model=FeedbackOut, summary="Create feedback")
async def create_feedback(
    request: Request,
    slug: str,
    payload: FeedbackCreate,
    current_user: Annotated[User, Depends(get_current_user)] = ...,
    db: Annotated[AsyncSession, Depends(get_db)] = ...,
):
    from app.domains.nodes.application.feedback_service import FeedbackService
    from app.domains.nodes.infrastructure.repositories.node_repository import (
        NodeRepository,
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
    service = FeedbackService(NodeRepository(db), notifier)
    return await service.create_feedback(
        db, slug, payload.content, payload.is_anonymous, current_user, author_id=current_user.id
    )


@router.delete("/{slug}/feedback/{feedback_id}", response_model=dict, summary="Delete feedback")
async def delete_feedback(
    request: Request,
    slug: str,
    feedback_id: UUID,
    current_user: Annotated[User, Depends(get_current_user)] = ...,
    db: Annotated[AsyncSession, Depends(get_db)] = ...,
):
    from app.domains.nodes.application.feedback_service import FeedbackService
    from app.domains.nodes.infrastructure.repositories.node_repository import (
        NodeRepository,
    )

    service = FeedbackService(NodeRepository(db))
    return await service.delete_feedback(
        db, slug, feedback_id, current_user, author_id=current_user.id
    )

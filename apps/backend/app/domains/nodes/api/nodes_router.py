from __future__ import annotations

from typing import List
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, Response, Header
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

from app.api.deps import get_current_user, get_current_user_optional, ensure_can_post, require_premium
from app.domains.nodes.application.query_models import (
    NodeFilterSpec,
    PageRequest,
    QueryContext,
)
from app.domains.nodes.infrastructure.queries.node_query_adapter import NodeQueryAdapter
from app.core.db.session import get_db
from app.domains.system.events import get_event_bus, NodeCreated, NodeUpdated
from app.domains.users.nft import user_has_nft
from app.domains.navigation.application.traces_service import TracesService
from app.domains.navigation.application.navigation_cache_service import NavigationCacheService
from app.domains.navigation.infrastructure.cache_adapter import CoreCacheAdapter
from app.core.config import settings
from app.core.log_events import cache_invalidate
from app.domains.nodes.infrastructure.models.node import Node
from app.domains.nodes.infrastructure.models.feedback import Feedback
from app.domains.tags.models import Tag
from app.domains.users.infrastructure.models.user import User
from app.domains.nodes.policies.node_policy import NodePolicy
from app.domains.nodes.schemas.feedback import FeedbackCreate, FeedbackOut
from app.domains.nodes.schemas.node import NodeCreate, NodeOut, NodeUpdate, ReactionUpdate
from app.domains.tags.schemas.node_tags import NodeTagsUpdate
from app.domains.nodes.infrastructure.repositories.node_repository import NodeRepositoryAdapter as NodeRepository

router = APIRouter(prefix="/nodes", tags=["nodes"])
navcache = NavigationCacheService(CoreCacheAdapter())


@router.get("", response_model=List[NodeOut], summary="List nodes")
async def list_nodes(
    response: Response,
    workspace_id: UUID,
    if_none_match: str | None = Header(None, alias="If-None-Match"),
    tags: str | None = Query(None),
    match: str = Query("any", pattern="^(any|all)$"),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> List[NodeOut]:
    tag_list = [t.strip() for t in tags.split(",") if t.strip()] if tags else None
    spec = NodeFilterSpec(tags=tag_list, match=match, workspace_id=workspace_id)
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
    payload: NodeCreate,
    workspace_id: UUID,
    current_user: User = Depends(ensure_can_post),
    db: AsyncSession = Depends(get_db),
):
    repo = NodeRepository(db)
    node = await repo.create(payload, current_user.id, workspace_id)
    await get_event_bus().publish(
        NodeCreated(node_id=node.id, slug=node.slug, author_id=current_user.id)
    )
    return {"slug": node.slug}


@router.get("/{slug}", response_model=NodeOut, summary="Get node")
async def read_node(
    slug: str,
    workspace_id: UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    repo = NodeRepository(db)
    node = await repo.get_by_slug(slug, workspace_id)
    if not node:
        raise HTTPException(status_code=404, detail="Node not found")
    NodePolicy.ensure_can_view(node, current_user)
    if node.premium_only:
        await require_premium(current_user)
    if node.nft_required and not await user_has_nft(current_user, node.nft_required):
        raise HTTPException(status_code=403, detail="NFT required")
    node = await repo.increment_views(node)
    await TracesService().maybe_add_auto_trace(db, node, current_user)
    return node


@router.post("/{node_id}/tags", response_model=NodeOut, summary="Set node tags")
async def set_node_tags(
    node_id: UUID,
    payload: NodeTagsUpdate,
    workspace_id: UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    repo = NodeRepository(db)
    node = await repo.get_by_id(node_id, workspace_id)
    if not node:
        raise HTTPException(status_code=404, detail="Node not found")
    NodePolicy.ensure_can_edit(node, current_user)
    node = await repo.set_tags(node, payload.tags, current_user.id)
    await get_event_bus().publish(
        NodeUpdated(
            node_id=node.id,
            slug=node.slug,
            author_id=current_user.id,
            tags_changed=True,
        )
    )
    return node


@router.patch("/{slug}", response_model=NodeOut, summary="Update node")
async def update_node(
    slug: str,
    payload: NodeUpdate,
    workspace_id: UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    repo = NodeRepository(db)
    node = await repo.get_by_slug(slug, workspace_id)
    if not node:
        raise HTTPException(status_code=404, detail="Node not found")
    NodePolicy.ensure_can_edit(node, current_user)
    was_public = node.is_public
    was_visible = node.is_visible
    node = await repo.update(node, payload, current_user.id)
    if was_public != node.is_public or was_visible != node.is_visible:
        await navcache.invalidate_navigation_by_node(slug)
        await navcache.invalidate_modes_by_node(slug)
        await navcache.invalidate_compass_all()
        cache_invalidate("nav", reason="node_update", key=slug)
        cache_invalidate("navm", reason="node_update", key=slug)
        cache_invalidate("comp", reason="node_update")
    tags_changed = payload.tags is not None
    await get_event_bus().publish(
        NodeUpdated(
            node_id=node.id,
            slug=node.slug,
            author_id=current_user.id,
            tags_changed=tags_changed,
        )
    )
    return node


@router.delete("/{slug}", summary="Delete node")
async def delete_node(
    slug: str,
    workspace_id: UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    repo = NodeRepository(db)
    node = await repo.get_by_slug(slug, workspace_id)
    if not node:
        raise HTTPException(status_code=404, detail="Node not found")
    NodePolicy.ensure_can_edit(node, current_user)
    await repo.delete(node)
    await navcache.invalidate_navigation_by_node(slug)
    await navcache.invalidate_modes_by_node(slug)
    await navcache.invalidate_compass_all()
    cache_invalidate("nav", reason="node_delete", key=slug)
    cache_invalidate("navm", reason="node_delete", key=slug)
    cache_invalidate("comp", reason="node_delete")
    return {"message": "Node deleted"}


@router.post("/{slug}/reactions", response_model=dict, summary="Update reactions")
async def update_reactions(
    slug: str,
    payload: ReactionUpdate,
    workspace_id: UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    from app.domains.nodes.application.reaction_service import ReactionService
    from app.domains.nodes.infrastructure.repositories.node_repository import NodeRepositoryAdapter
    service = ReactionService(NodeRepositoryAdapter(db), navcache)
    return await service.update_reactions_by_slug(
        db,
        slug,
        payload.reaction,
        payload.action,
        workspace_id=workspace_id,
        actor_id=str(current_user.id),
    )


@router.get("/{slug}/feedback", response_model=List[FeedbackOut], summary="List feedback")
async def list_feedback(
    slug: str,
    workspace_id: UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    from app.domains.nodes.application.feedback_service import FeedbackService
    from app.domains.nodes.infrastructure.repositories.node_repository import NodeRepositoryAdapter
    service = FeedbackService(NodeRepositoryAdapter(db))
    return await service.list_feedback(db, slug, current_user, workspace_id)


@router.post("/{slug}/feedback", response_model=FeedbackOut, summary="Create feedback")
async def create_feedback(
    slug: str,
    payload: FeedbackCreate,
    workspace_id: UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    from app.domains.nodes.application.feedback_service import FeedbackService
    from app.domains.nodes.infrastructure.repositories.node_repository import NodeRepositoryAdapter
    from app.domains.notifications.application.notify_service import NotifyService
    from app.domains.notifications.infrastructure.repositories.notification_repository import NotificationRepository
    from app.domains.notifications.infrastructure.transports.websocket import WebsocketPusher, manager as ws_manager

    notifier = NotifyService(NotificationRepository(db), WebsocketPusher(ws_manager))
    service = FeedbackService(NodeRepositoryAdapter(db), notifier)
    return await service.create_feedback(db, slug, payload.content, payload.is_anonymous, current_user, workspace_id)


@router.delete("/{slug}/feedback/{feedback_id}", response_model=dict, summary="Delete feedback")
async def delete_feedback(
    slug: str,
    feedback_id: UUID,
    workspace_id: UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    from app.domains.nodes.application.feedback_service import FeedbackService
    from app.domains.nodes.infrastructure.repositories.node_repository import NodeRepositoryAdapter
    service = FeedbackService(NodeRepositoryAdapter(db))
    return await service.delete_feedback(db, slug, feedback_id, current_user, workspace_id)

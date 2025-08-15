from datetime import datetime
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

from app.api.deps import ensure_can_post, get_current_user, require_premium
from app.db.session import get_db
from app.engine.embedding import update_node_embedding
from app.engine.transitions import get_transitions
from app.engine.random import get_random_node
from app.engine.transition_controller import apply_mode
from app.engine.echo import record_echo_trace
from app.engine.traces import maybe_add_auto_trace
from app.services.query import (
    NodeFilterSpec,
    NodeQueryService,
    PageRequest,
    QueryContext,
)
from app.services.nft import user_has_nft
from app.services.navcache import navcache
from app.services.events import get_event_bus, NodeCreated, NodeUpdated
from app.core.config import settings
from app.models.node import Node
from app.models.feedback import Feedback
from app.models.user import User
from app.schemas.node import NodeCreate, NodeOut, NodeUpdate, ReactionUpdate
from app.schemas.tag import NodeTagsUpdate
from app.schemas.feedback import FeedbackCreate, FeedbackOut
from app.schemas.transition import (
    NodeTransitionCreate,
    NextTransitions,
    TransitionOption,
    TransitionController,
    TransitionMode,
    NextModes,
    AvailableMode,
)
from app.services.quests import check_quest_completion
from app.policies import NodePolicy
from app.repositories import NodeRepository, TransitionRepository
from app.core.log_events import cache_invalidate

router = APIRouter(prefix="/nodes", tags=["nodes"])


@router.get("", response_model=list[NodeOut], summary="List nodes")
async def list_nodes(
    tags: str | None = Query(None),
    match: str = Query("any", pattern="^(any|all)$"),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """List visible nodes for the current user with optional tag filtering."""
    tag_list = [t.strip() for t in tags.split(",") if t.strip()] if tags else None
    spec = NodeFilterSpec(tags=tag_list, match=match)
    ctx = QueryContext(user=current_user, is_admin=False)
    service = NodeQueryService(db)
    nodes = await service.list_nodes(spec, PageRequest(), ctx)
    return nodes


@router.post("", response_model=dict, summary="Create node")
async def create_node(
    payload: NodeCreate,
    current_user: User = Depends(ensure_can_post),
    db: AsyncSession = Depends(get_db),
):
    """Create a new node authored by the current user."""
    repo = NodeRepository(db)
    node = await repo.create(payload, current_user.id)
    await get_event_bus().publish(
        NodeCreated(node_id=node.id, slug=node.slug, author_id=current_user.id)
    )
    return {"slug": node.slug}


@router.get("/{slug}", response_model=NodeOut, summary="Get node")
async def read_node(
    slug: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Retrieve a node by its slug."""
    repo = NodeRepository(db)
    node = await repo.get_by_slug(slug)
    if not node:
        raise HTTPException(status_code=404, detail="Node not found")
    NodePolicy.ensure_can_view(node, current_user)
    if node.premium_only:
        await require_premium(current_user)
    if node.nft_required and not await user_has_nft(current_user, node.nft_required):
        raise HTTPException(status_code=403, detail="NFT required")
    node = await repo.increment_views(node)
    await check_quest_completion(db, current_user, node)
    await maybe_add_auto_trace(db, node, current_user)
    return node


@router.post("/{node_id}/tags", response_model=NodeOut, summary="Set node tags")
async def set_node_tags(
    node_id: UUID,
    payload: NodeTagsUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Replace the list of tags associated with a node."""
    repo = NodeRepository(db)
    node = await repo.get_by_id(node_id)
    if not node:
        raise HTTPException(status_code=404, detail="Node not found")
    NodePolicy.ensure_can_edit(node, current_user)
    node = await repo.set_tags(node, payload.tags)
    await get_event_bus().publish(
        NodeUpdated(
            node_id=node.id,
            slug=node.slug,
            author_id=current_user.id,
            tags_changed=True,
        )
    )
    return node


@router.post(
    "/{slug}/visit/{to_slug}",
    response_model=dict,
    summary="Record visit",
)
async def record_visit(
    slug: str,
    to_slug: str,
    source: str | None = None,
    channel: str | None = None,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Record a manual visit from one node to another."""
    repo = NodeRepository(db)
    from_node = await repo.get_by_slug(slug)
    if not from_node:
        raise HTTPException(status_code=404, detail="Node not found")
    to_node = await repo.get_by_slug(to_slug)
    if not to_node:
        raise HTTPException(status_code=404, detail="Target node not found")
    await record_echo_trace(db, from_node, to_node, current_user, source=source, channel=channel)
    return {"status": "ok"}


@router.get(
    "/{slug}/echo",
    dependencies=[Depends(require_premium)],
    summary="Echo transition",
)
async def view_echo(slug: str):
    """Return a placeholder echo response for premium users."""
    return {"slug": slug}


@router.post(
    "/{slug}/transitions",
    response_model=dict,
    summary="Create transition",
)
async def create_transition(
    slug: str,
    payload: NodeTransitionCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Add a manual transition from one node to another."""
    repo = NodeRepository(db)
    from_node = await repo.get_by_slug(slug)
    if not from_node:
        raise HTTPException(status_code=404, detail="Node not found")
    NodePolicy.ensure_can_edit(from_node, current_user)
    to_node = await repo.get_by_slug(payload.to_slug)
    if not to_node:
        raise HTTPException(status_code=404, detail="Target node not found")
    t_repo = TransitionRepository(db)
    transition = await t_repo.create(from_node.id, to_node.id, payload, current_user.id)
    await navcache.invalidate_navigation_by_node(slug)
    cache_invalidate("nav", reason="transition_create", key=slug)
    return {"id": str(transition.id)}


@router.get(
    "/{slug}/next",
    response_model=NextTransitions,
    summary="Next transitions",
)
async def get_next_nodes(
    slug: str,
    mode: str = Query("auto"),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Compute possible next nodes from the given node."""
    repo = NodeRepository(db)
    node = await repo.get_by_slug(slug)
    if not node:
        raise HTTPException(status_code=404, detail="Node not found")

    controller_data = node.meta.get("transition_controller") or {}
    try:
        controller = TransitionController.model_validate(controller_data)
    except Exception:
        controller = TransitionController()

    def find_mode(name: str) -> TransitionMode | None:
        for m in controller.modes:
            if m.mode == name:
                return m
        return None

    async def run_mode(m: TransitionMode) -> list[TransitionOption]:
        return await apply_mode(db, node, current_user, m, controller.max_options)

    user_id = str(current_user.id)
    if settings.cache.enable_nav_cache:
        cached = await navcache.get_navigation(user_id, slug, mode)
        if cached:
            return NextTransitions(**cached)

    # Determine active mode
    if mode == "auto":
        if controller.default_mode != "auto":
            mode = controller.default_mode
        else:
            for m in controller.modes:
                opts = await run_mode(m)
                if opts:
                    result_obj = NextTransitions(mode=m.mode, transitions=opts)
                    if settings.cache.enable_nav_cache:
                        await navcache.set_navigation(
                            user_id,
                            slug,
                            mode,
                            result_obj.model_dump(),
                            settings.cache.nav_cache_ttl,
                        )
                    return result_obj
            result_obj = NextTransitions(mode="auto", transitions=[])
            if settings.cache.enable_nav_cache:
                await navcache.set_navigation(
                    user_id,
                    slug,
                    mode,
                    result_obj.model_dump(),
                    settings.cache.nav_cache_ttl,
                )
            return result_obj

    m = find_mode(mode)
    if m:
        opts = await run_mode(m)
        result_obj = NextTransitions(mode=m.mode, transitions=opts)
        if settings.cache.enable_nav_cache:
            await navcache.set_navigation(
                user_id,
                slug,
                mode,
                result_obj.model_dump(),
                settings.cache.nav_cache_ttl,
            )
        return result_obj

    # Fallback to previous behaviour if no DSL modes defined
    transitions: list[TransitionOption] = []
    found = await get_transitions(db, node, current_user)
    if found:
        transitions = [
            TransitionOption(slug=t.to_node.slug, label=t.label, mode=t.type.value)
            for t in found[: controller.max_options]
        ]
        result_obj = NextTransitions(mode="manual", transitions=transitions)
        if settings.cache.enable_nav_cache:
            await navcache.set_navigation(
                user_id,
                slug,
                mode,
                result_obj.model_dump(),
                settings.cache.nav_cache_ttl,
            )
        return result_obj
    rnd = await get_random_node(db, user=current_user, exclude_node_id=node.id)
    if rnd:
        transitions = [TransitionOption(slug=rnd.slug, label=rnd.title, mode="random")]
    result_obj = NextTransitions(mode="random", transitions=transitions)
    if settings.cache.enable_nav_cache:
        await navcache.set_navigation(
            user_id, slug, mode, result_obj.model_dump(), settings.cache.nav_cache_ttl
        )
    return result_obj


@router.get(
    "/{slug}/next_modes",
    response_model=NextModes,
    summary="Available modes",
)
async def get_next_modes(
    slug: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """List navigation modes available for the node."""
    repo = NodeRepository(db)
    node = await repo.get_by_slug(slug)
    if not node:
        raise HTTPException(status_code=404, detail="Node not found")
    controller_data = node.meta.get("transition_controller") or {}
    try:
        controller = TransitionController.model_validate(controller_data)
    except Exception:
        controller = TransitionController()
    user_id = str(current_user.id)
    if settings.cache.enable_nav_cache:
        cached = await navcache.get_modes(user_id, slug)
        if cached:
            return NextModes(**cached)
    modes = [AvailableMode(mode=m.mode, label=m.label) for m in controller.modes]
    result_obj = NextModes(default_mode=controller.default_mode, modes=modes)
    if settings.cache.enable_nav_cache:
        await navcache.set_modes(
            user_id, slug, result_obj.model_dump(), settings.cache.nav_cache_ttl
        )
    return result_obj


@router.patch("/{slug}", response_model=NodeOut, summary="Update node")
async def update_node(
    slug: str,
    payload: NodeUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Update attributes of an existing node."""
    repo = NodeRepository(db)
    node = await repo.get_by_slug(slug)
    if not node:
        raise HTTPException(status_code=404, detail="Node not found")
    NodePolicy.ensure_can_edit(node, current_user)
    node = await repo.update(node, payload)
    await navcache.invalidate_navigation_by_node(slug)
    await navcache.invalidate_modes_by_node(slug)
    await navcache.invalidate_compass_all()
    cache_invalidate("nav", reason="node_update", key=slug)
    cache_invalidate("navm", reason="node_update", key=slug)
    cache_invalidate("comp", reason="node_update")
    return node


@router.delete("/{slug}", summary="Delete node")
async def delete_node(
    slug: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Remove a node created by the current user."""
    repo = NodeRepository(db)
    node = await repo.get_by_slug(slug)
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


@router.post(
    "/{slug}/reactions",
    response_model=dict,
    summary="Update reactions",
)
async def update_reactions(
    slug: str,
    payload: ReactionUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Add or remove reactions on a node."""
    repo = NodeRepository(db)
    node = await repo.get_by_slug(slug)
    if not node:
        raise HTTPException(status_code=404, detail="Node not found")
    node = await repo.update_reactions(node, payload.reaction, payload.action)
    await navcache.invalidate_compass_all()
    cache_invalidate("comp", reason="reaction_update", key=slug)
    return {"reactions": node.reactions}


@router.get(
    "/{slug}/feedback",
    response_model=list[FeedbackOut],
    summary="List feedback",
)
async def list_feedback(
    slug: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Return feedback entries for a node."""
    repo = NodeRepository(db)
    node = await repo.get_by_slug(slug)
    if not node:
        raise HTTPException(status_code=404, detail="Node not found")
    if not node.allow_feedback and node.author_id != current_user.id:
        raise HTTPException(status_code=403, detail="Feedback disabled")
    result = await db.execute(
        select(Feedback).where(Feedback.node_id == node.id, Feedback.is_hidden == False)
    )
    return result.scalars().all()


@router.post(
    "/{slug}/feedback",
    response_model=FeedbackOut,
    summary="Create feedback",
)
async def create_feedback(
    slug: str,
    payload: FeedbackCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Create a feedback entry for a node."""
    repo = NodeRepository(db)
    node = await repo.get_by_slug(slug)
    if not node:
        raise HTTPException(status_code=404, detail="Node not found")
    if not node.allow_feedback:
        raise HTTPException(status_code=403, detail="Feedback disabled")
    if not node.is_public and node.author_id != current_user.id:
        raise HTTPException(
            status_code=403, detail="Not authorized to comment on this node"
        )
    feedback = Feedback(
        node_id=node.id,
        author_id=current_user.id,
        content=payload.content,
        is_anonymous=payload.is_anonymous,
    )
    db.add(feedback)
    await db.commit()
    await db.refresh(feedback)
    return feedback


@router.delete(
    "/{slug}/feedback/{feedback_id}",
    response_model=dict,
    summary="Delete feedback",
)
async def delete_feedback(
    slug: str,
    feedback_id: UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Hide a feedback item authored by the current user or node owner."""
    repo = NodeRepository(db)
    node = await repo.get_by_slug(slug)
    if not node:
        raise HTTPException(status_code=404, detail="Node not found")
    result = await db.execute(
        select(Feedback).where(Feedback.id == feedback_id, Feedback.node_id == node.id)
    )
    feedback = result.scalars().first()
    if not feedback:
        raise HTTPException(status_code=404, detail="Feedback not found")
    if current_user.id not in (node.author_id, feedback.author_id):
        raise HTTPException(status_code=403, detail="Not authorized")
    feedback.is_hidden = True
    await db.commit()
    return {"status": "ok"}

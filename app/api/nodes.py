from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

from app.api.deps import (
    ensure_can_post,
    get_current_user,
    require_premium,
)
from app.db.session import get_db
from app.engine.transitions import get_transitions
from app.engine.random import get_random_node
from app.engine.transition_controller import apply_mode
from app.engine.embedding import update_node_embedding
from app.engine.echo import record_echo_trace
from app.models.node import Node
from app.models.transition import NodeTransition, NodeTransitionType
from app.models.user import User
from app.schemas.node import NodeCreate, NodeOut, NodeUpdate, ReactionUpdate
from app.schemas.transition import (
    NodeTransitionCreate,
    NextTransitions,
    TransitionOption,
    TransitionController,
    TransitionMode,
    NextModes,
    AvailableMode,
)

router = APIRouter(prefix="/nodes", tags=["nodes"])


@router.post("", response_model=dict)
async def create_node(
    payload: NodeCreate,
    current_user: User = Depends(ensure_can_post),
    db: AsyncSession = Depends(get_db),
):
    node = Node(
        title=payload.title,
        content_format=payload.content_format,
        content=payload.content,
        media=payload.media or [],
        tags=payload.tags or [],
        is_public=payload.is_public,
        meta=payload.meta or {},
        premium_only=payload.premium_only if payload.premium_only is not None else False,
        nft_required=payload.nft_required,
        ai_generated=payload.ai_generated if payload.ai_generated is not None else False,
        author_id=current_user.id,
    )
    db.add(node)
    await db.commit()
    await db.refresh(node)
    await update_node_embedding(db, node)
    return {"slug": node.slug}


@router.get("/{slug}", response_model=NodeOut)
async def read_node(
    slug: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(select(Node).where(Node.slug == slug, Node.is_visible == True))
    node = result.scalars().first()
    if not node:
        raise HTTPException(status_code=404, detail="Node not found")
    if not node.is_public and node.author_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not authorized to view this node")
    if node.premium_only:
        await require_premium(current_user)
    node.views += 1
    await db.commit()
    await db.refresh(node)
    return node



@router.post("/{slug}/visit/{to_slug}", response_model=dict)
async def record_visit(
    slug: str,
    to_slug: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(select(Node).where(Node.slug == slug))
    from_node = result.scalars().first()
    if not from_node:
        raise HTTPException(status_code=404, detail="Node not found")
    result = await db.execute(select(Node).where(Node.slug == to_slug))
    to_node = result.scalars().first()
    if not to_node:
        raise HTTPException(status_code=404, detail="Target node not found")
    await record_echo_trace(db, from_node, to_node, current_user)
    return {"status": "ok"}


@router.get("/{slug}/echo", dependencies=[Depends(require_premium)])
async def view_echo(slug: str):
    return {"slug": slug}


@router.post("/{slug}/transitions", response_model=dict)
async def create_transition(
    slug: str,
    payload: NodeTransitionCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(select(Node).where(Node.slug == slug))
    from_node = result.scalars().first()
    if not from_node:
        raise HTTPException(status_code=404, detail="Node not found")
    if from_node.author_id != current_user.id and current_user.role not in (
        "moderator",
        "admin",
    ):
        raise HTTPException(status_code=403, detail="Not allowed")
    result = await db.execute(select(Node).where(Node.slug == payload.to_slug))
    to_node = result.scalars().first()
    if not to_node:
        raise HTTPException(status_code=404, detail="Target node not found")
    transition = NodeTransition(
        from_node_id=from_node.id,
        to_node_id=to_node.id,
        type=NodeTransitionType(payload.type),
        condition=payload.condition or {},
        weight=payload.weight,
        label=payload.label,
        created_by=current_user.id,
    )
    db.add(transition)
    await db.commit()
    await db.refresh(transition)
    return {"id": str(transition.id)}


@router.get("/{slug}/next", response_model=NextTransitions)
async def get_next_nodes(
    slug: str,
    mode: str = Query("auto"),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(select(Node).where(Node.slug == slug))
    node = result.scalars().first()
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

    # Determine active mode
    if mode == "auto":
        if controller.default_mode != "auto":
            mode = controller.default_mode
        else:
            for m in controller.modes:
                opts = await run_mode(m)
                if opts:
                    return NextTransitions(mode=m.mode, transitions=opts)
            return NextTransitions(mode="auto", transitions=[])

    m = find_mode(mode)
    if m:
        opts = await run_mode(m)
        return NextTransitions(mode=m.mode, transitions=opts)

    # Fallback to previous behaviour if no DSL modes defined
    transitions: list[TransitionOption] = []
    found = await get_transitions(db, node, current_user)
    if found:
        transitions = [
            TransitionOption(slug=t.to_node.slug, label=t.label, mode=t.type.value)
            for t in found[: controller.max_options]
        ]
        return NextTransitions(mode="manual", transitions=transitions)
    rnd = await get_random_node(db, exclude_node_id=node.id)
    if rnd:
        transitions = [
            TransitionOption(slug=rnd.slug, label=rnd.title, mode="random")
        ]
    return NextTransitions(mode="random", transitions=transitions)


@router.get("/{slug}/next_modes", response_model=NextModes)
async def get_next_modes(
    slug: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(select(Node).where(Node.slug == slug))
    node = result.scalars().first()
    if not node:
        raise HTTPException(status_code=404, detail="Node not found")
    controller_data = node.meta.get("transition_controller") or {}
    try:
        controller = TransitionController.model_validate(controller_data)
    except Exception:
        controller = TransitionController()
    modes = [AvailableMode(mode=m.mode, label=m.label) for m in controller.modes]
    return NextModes(default_mode=controller.default_mode, modes=modes)


@router.patch("/{slug}", response_model=NodeOut)
async def update_node(
    slug: str,
    payload: NodeUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(select(Node).where(Node.slug == slug))
    node = result.scalars().first()
    if not node:
        raise HTTPException(status_code=404, detail="Node not found")
    if node.author_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not authorized to edit this node")
    data = payload.dict(exclude_unset=True)
    for field, value in data.items():
        setattr(node, field, value)
    node.updated_at = datetime.utcnow()
    await db.commit()
    await db.refresh(node)
    await update_node_embedding(db, node)
    return node


@router.delete("/{slug}")
async def delete_node(
    slug: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(select(Node).where(Node.slug == slug))
    node = result.scalars().first()
    if not node:
        raise HTTPException(status_code=404, detail="Node not found")
    if node.author_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not authorized to delete this node")
    await db.delete(node)
    await db.commit()
    return {"message": "Node deleted"}


@router.post("/{slug}/reactions", response_model=dict)
async def update_reactions(
    slug: str,
    payload: ReactionUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(select(Node).where(Node.slug == slug))
    node = result.scalars().first()
    if not node:
        raise HTTPException(status_code=404, detail="Node not found")
    reactions = node.reactions or {}
    current = reactions.get(payload.reaction, 0)
    if payload.action == "add":
        reactions[payload.reaction] = current + 1
    elif payload.action == "remove" and current > 0:
        reactions[payload.reaction] = current - 1
        if reactions[payload.reaction] <= 0:
            reactions.pop(payload.reaction)
    node.reactions = reactions
    await db.commit()
    await db.refresh(node)
    return {"reactions": node.reactions}

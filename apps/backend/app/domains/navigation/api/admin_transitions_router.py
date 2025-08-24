from __future__ import annotations

from uuid import UUID
from dataclasses import dataclass, asdict
from types import SimpleNamespace

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

from app.core.db.transition_query import TransitionFilterSpec, TransitionQueryService
from app.domains.nodes.application.query_models import PageRequest, QueryContext
from app.core.db.session import get_db
from app.domains.navigation.application.navigation_cache_service import (
    NavigationCacheService,
)
from app.domains.navigation.application.transition_router import (
    RandomPolicy,
    TransitionProvider,
    TransitionRouter,
)
from app.domains.navigation.infrastructure.cache_adapter import CoreCacheAdapter
from app.domains.nodes.infrastructure.models.node import Node
from app.domains.navigation.infrastructure.models.transition_models import (
    NodeTransition,
    NodeTransitionType,
)
from app.domains.navigation.schemas.transitions import (
    AdminTransitionOut,
    NodeTransitionUpdate,
    TransitionDisableRequest,
)
from app.security import ADMIN_AUTH_RESPONSES, require_admin_role

router = APIRouter(
    prefix="/admin/transitions", tags=["admin"], responses=ADMIN_AUTH_RESPONSES
)
admin_required = require_admin_role()
navcache = NavigationCacheService(CoreCacheAdapter())


@router.get("", response_model=list[AdminTransitionOut], summary="List transitions")
async def list_transitions_admin(
    from_slug: str | None = Query(None, alias="from"),
    to_slug: str | None = Query(None, alias="to"),
    type: NodeTransitionType | None = None,
    author: UUID | None = None,
    page: int = 1,
    page_size: int = Query(50, ge=1, le=100),
    current_user=Depends(admin_required),
    db: AsyncSession = Depends(get_db),
):
    spec = TransitionFilterSpec(
        from_slug=from_slug, to_slug=to_slug, type=type, author=author
    )
    ctx = QueryContext(user=current_user, is_admin=True)
    svc = TransitionQueryService(db)
    rows = await svc.list_transitions(
        spec, PageRequest(limit=page_size, offset=(page - 1) * page_size), ctx
    )
    return [
        AdminTransitionOut(
            id=t.id,
            from_slug=fs,
            to_slug=ts,
            type=t.type,
            weight=t.weight,
            label=t.label,
            created_by=t.created_by,
            created_at=t.created_at,
        )
        for t, fs, ts in rows
    ]


@router.patch(
    "/{transition_id}", response_model=AdminTransitionOut, summary="Update transition"
)
async def update_transition_admin(
    transition_id: UUID,
    payload: NodeTransitionUpdate,
    current_user=Depends(admin_required),
    db: AsyncSession = Depends(get_db),
):
    transition = await db.get(NodeTransition, transition_id)
    if not transition:
        raise HTTPException(status_code=404, detail="Transition not found")

    old_from = await db.get(Node, transition.from_node_id)
    old_from_slug = old_from.slug if old_from else None

    if payload.from_slug:
        res = await db.execute(select(Node).where(Node.slug == payload.from_slug))
        new_from = res.scalars().first()
        if not new_from:
            raise HTTPException(status_code=404, detail="Source node not found")
        transition.from_node_id = new_from.id
    if payload.to_slug:
        res = await db.execute(select(Node).where(Node.slug == payload.to_slug))
        new_to = res.scalars().first()
        if not new_to:
            raise HTTPException(status_code=404, detail="Target node not found")
        transition.to_node_id = new_to.id
    if payload.type:
        transition.type = payload.type
    if payload.condition is not None:
        transition.condition = payload.condition.model_dump(exclude_none=True)
    if payload.weight is not None:
        transition.weight = payload.weight
    if payload.label is not None:
        transition.label = payload.label

    await db.commit()
    await db.refresh(transition)

    from_node = await db.get(Node, transition.from_node_id)
    from_slug = from_node.slug if from_node else old_from_slug

    await navcache.invalidate_navigation_by_node(from_slug)
    await navcache.invalidate_compass_by_node(from_slug)

    to_node = await db.get(Node, transition.to_node_id)
    return AdminTransitionOut(
        id=transition.id,
        from_slug=from_node.slug if from_node else "",
        to_slug=to_node.slug if to_node else "",
        type=transition.type,
        weight=transition.weight,
        label=transition.label,
        created_by=transition.created_by,
        created_at=transition.created_at,
    )


@router.delete("/{transition_id}", summary="Delete transition")
async def delete_transition_admin(
    transition_id: UUID,
    current_user=Depends(admin_required),
    db: AsyncSession = Depends(get_db),
):
    transition = await db.get(NodeTransition, transition_id)
    if not transition:
        raise HTTPException(status_code=404, detail="Transition not found")
    from_node = await db.get(Node, transition.from_node_id)
    from_slug = from_node.slug if from_node else None
    await db.delete(transition)
    await db.commit()
    if from_slug:
        await navcache.invalidate_navigation_by_node(from_slug)
        await navcache.invalidate_compass_by_node(from_slug)
    return {"message": "Transition deleted"}


@router.post("/disable_by_node", summary="Disable transitions by node")
async def disable_transitions_by_node(
    payload: TransitionDisableRequest,
    current_user=Depends(admin_required),
    db: AsyncSession = Depends(get_db),
):
    res = await db.execute(select(Node).where(Node.slug == payload.slug))
    node = res.scalars().first()
    if not node:
        raise HTTPException(status_code=404, detail="Node not found")
    stmt = select(NodeTransition).where(
        (NodeTransition.from_node_id == node.id)
        | (NodeTransition.to_node_id == node.id)
    )
    res = await db.execute(stmt)
    transitions = res.scalars().all()
    for t in transitions:
        t.type = NodeTransitionType.locked
    await db.commit()
    await navcache.invalidate_navigation_by_node(node.slug)
    await navcache.invalidate_compass_by_node(node.slug)
    return {"disabled": len(transitions)}


class SimulateRequest(BaseModel):
    start: str
    graph: dict[str, list[str]]
    steps: int = 1
    seed: int | None = None


@dataclass
class _DummyNode:
    slug: str
    workspace_id: str = "sim"


class _DictProvider(TransitionProvider):
    def __init__(self, mapping: dict[str, list[str]]):
        self.mapping = mapping

    async def get_transitions(self, db, node, user, workspace_id):
        return [_DummyNode(s) for s in self.mapping.get(node.slug, [])]


@router.post("/simulate", summary="Simulate transitions")
async def simulate_transitions(
    payload: SimulateRequest, current_user=Depends(admin_required)
):
    provider = _DictProvider(payload.graph)
    policies = [RandomPolicy(provider)]
    router = TransitionRouter(policies, not_repeat_last=5)
    start = _DummyNode(payload.start)
    budget = SimpleNamespace(
        max_time_ms=1000, max_queries=1000, max_filters=1000, fallback_chain=[]
    )
    current = start
    traces: list[dict] = []
    route: list[str] = [start.slug]
    for _ in range(payload.steps):
        res = await router.route(None, current, None, budget, seed=payload.seed)
        traces.extend(asdict(t) for t in res.trace)
        if res.next is None:
            break
        current = res.next
        route.append(current.slug)
    return {"route": route, "trace": traces}

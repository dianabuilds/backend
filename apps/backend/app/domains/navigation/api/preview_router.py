from __future__ import annotations

import math
from dataclasses import asdict
from typing import Annotated, Any
from uuid import UUID, uuid4

from fastapi import APIRouter, Depends, HTTPException, Request
from pydantic import BaseModel, ConfigDict
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

from app.core.db.session import get_db

from app.core.preview import PreviewContext, PreviewMode  # isort: skip
from app.core.metrics import record_no_route, record_route_length
from app.core.rng import next_seed
from app.domains.navigation.application.navigation_service import NavigationService
from app.domains.navigation.application.transition_router import (
    NoRouteReason,
    _compute_entropy,
)
from app.domains.nodes.infrastructure.models.node import Node
from app.security import (
    ADMIN_AUTH_RESPONSES,
    create_preview_token,
    require_admin_or_preview_token,
    require_admin_role,
)


class SimulateRequest(BaseModel):
    workspace_id: UUID
    start: str
    mode: str | None = None
    params: dict[str, Any] | None = None
    history: list[str] | None = None
    seed: int | None = None
    preview_mode: PreviewMode = "off"

    model_config = ConfigDict(extra="allow")


class PreviewLinkRequest(BaseModel):
    workspace_id: UUID
    ttl: int | None = None


router = APIRouter(
    prefix="/admin/preview",
    tags=["admin"],
    responses=ADMIN_AUTH_RESPONSES,
)


@router.post("/link", dependencies=[Depends(require_admin_role())])
async def create_preview_link(payload: PreviewLinkRequest) -> dict[str, str]:
    preview_session_id = uuid4().hex
    token = create_preview_token(
        preview_session_id, str(payload.workspace_id), ttl=payload.ttl
    )
    return {"url": f"/preview?token={token}"}


@router.get("/link", dependencies=[Depends(require_admin_role())])
async def create_preview_link_get(
    workspace_id: UUID, ttl: int | None = None
) -> dict[str, str]:
    payload = PreviewLinkRequest(workspace_id=workspace_id, ttl=ttl)
    return await create_preview_link(payload)


@router.post(
    "/transitions/simulate",
    summary="Simulate transitions with preview",
    dependencies=[Depends(require_admin_or_preview_token())],
)
async def simulate_transitions(
    payload: SimulateRequest,
    db: Annotated[AsyncSession, Depends(get_db)] = ...,  # noqa: B008
    request: Request = None,
):
    result = await db.execute(
        select(Node).where(
            Node.workspace_id == payload.workspace_id,
            Node.slug == payload.start,
        )
    )
    node = result.scalars().first()
    if not node:
        raise HTTPException(status_code=404, detail="Node not found")

    if request and hasattr(request.state, "preview_token"):
        token_ws = request.state.preview_token.get("workspace_id")
        if str(payload.workspace_id) != str(token_ws):
            raise HTTPException(status_code=403, detail="Invalid workspace")

    svc = NavigationService()
    if payload.history:
        svc._router.history.extend(payload.history)

    seed = payload.seed if payload.seed is not None else next_seed()
    preview = PreviewContext(mode=payload.preview_mode, seed=seed)
    res = await svc.build_route(db, node, None, preview=preview)
    tags = [getattr(t, "slug", t) for t in getattr(res.next, "tags", []) or []]
    tag_entropy = _compute_entropy(tags)
    chosen_trace = next((t for t in res.trace if t.chosen), None)
    sources = [chosen_trace.policy] if chosen_trace and chosen_trace.policy else []
    source_diversity = 0.0
    if sources:
        counts = {s: sources.count(s) for s in set(sources)}
        total = sum(counts.values())
        source_diversity = -sum(
            (c / total) * math.log(c / total) for c in counts.values()
        )
    if res.reason == NoRouteReason.NO_ROUTE:
        record_no_route(str(payload.workspace_id), preview=True)
    else:
        record_route_length(
            len(svc._router.history), str(payload.workspace_id), preview=True
        )
    return {
        "next": res.next.slug if res.next else None,
        "reason": res.reason.value if res.reason else None,
        "trace": [asdict(t) for t in res.trace],
        "metrics": {
            **res.metrics,
            "tag_entropy": tag_entropy,
            "source_diversity": source_diversity,
            "tags": tags,
            "sources": sources,
        },
        "seed": seed,
    }

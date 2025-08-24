from __future__ import annotations

from dataclasses import asdict
from uuid import UUID, uuid4
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Request
from pydantic import BaseModel, ConfigDict
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

from app.core.db.session import get_db
from app.core.preview import PreviewContext, PreviewMode
from app.domains.navigation.application.navigation_service import NavigationService
from app.domains.nodes.infrastructure.models.node import Node
from app.security import (
    ADMIN_AUTH_RESPONSES,
    require_admin_role,
    require_admin_or_preview_token,
    create_preview_token,
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


@router.post(
    "/transitions/simulate",
    summary="Simulate transitions with preview",
    dependencies=[Depends(require_admin_or_preview_token())],
)
async def simulate_transitions(
    payload: SimulateRequest,
    db: AsyncSession = Depends(get_db),
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

    preview = PreviewContext(mode=payload.preview_mode, seed=payload.seed)
    res = await svc.build_route(db, node, None, preview=preview)
    return {
        "next": res.next.slug if res.next else None,
        "reason": res.reason.value if res.reason else None,
        "trace": [asdict(t) for t in res.trace],
        "metrics": res.metrics,
    }

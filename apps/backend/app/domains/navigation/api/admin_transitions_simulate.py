from __future__ import annotations

from dataclasses import asdict

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, ConfigDict
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

from app.core.db.session import get_db
from app.core.preview import PreviewContext, PreviewMode
from app.domains.navigation.application.navigation_service import NavigationService
from app.domains.nodes.infrastructure.models.node import Node
from app.security import ADMIN_AUTH_RESPONSES, require_admin_role


class SimulateRequest(BaseModel):
    start: str
    mode: str | None = None
    history: list[str] | None = None
    seed: int | None = None
    preview_mode: PreviewMode = "off"

    model_config = ConfigDict(extra="allow")


router = APIRouter(
    prefix="/admin/transitions",
    tags=["admin"],
    responses=ADMIN_AUTH_RESPONSES,
)
admin_required = require_admin_role()


@router.post("/simulate", summary="Simulate transitions")
async def simulate_transitions(
    payload: SimulateRequest,
    current_user=Depends(admin_required),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(select(Node).where(Node.slug == payload.start))
    node = result.scalars().first()
    if not node:
        raise HTTPException(status_code=404, detail="Node not found")

    svc = NavigationService()
    if payload.history:
        svc._router.history.extend(payload.history)

    preview = PreviewContext(mode=payload.preview_mode, seed=payload.seed)
    res = await svc.build_route(db, node, current_user, preview=preview)
    return {
        "next": res.next.slug if res.next else None,
        "reason": res.reason.value if res.reason else None,
        "trace": [asdict(t) for t in res.trace],
        "metrics": res.metrics,
    }

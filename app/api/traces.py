from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter, Depends, Query, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy import or_

from app.db.session import get_db
from app.api.deps import get_current_user
from app.models.node import Node
from app.models.node_trace import NodeTrace, NodeTraceVisibility
from app.models.user import User
from app.schemas.trace import NodeTraceCreate, NodeTraceOut

router = APIRouter(prefix="/traces", tags=["traces"])


@router.post("", response_model=NodeTraceOut, summary="Create trace")
async def create_trace(
    payload: NodeTraceCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Create a new user trace for a node."""
    node = await db.get(Node, payload.node_id)
    if not node:
        raise HTTPException(status_code=404, detail="Node not found")
    trace = NodeTrace(
        node_id=node.id,
        user_id=current_user.id,
        kind=payload.kind,
        comment=payload.comment,
        tags=payload.tags,
        visibility=payload.visibility,
    )
    db.add(trace)
    await db.commit()
    await db.refresh(trace)
    return trace


@router.get("", response_model=list[NodeTraceOut], summary="List traces")
async def list_traces(
    node_id: UUID = Query(...),
    visible_to: str = Query("all", pattern="^(all|me)$"),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Return traces for a node with optional visibility filtering."""
    stmt = select(NodeTrace).where(NodeTrace.node_id == node_id)
    if visible_to == "me":
        stmt = stmt.where(
            or_(
                NodeTrace.visibility.in_([NodeTraceVisibility.public, NodeTraceVisibility.system]),
                NodeTrace.user_id == current_user.id,
            )
        )
    else:
        stmt = stmt.where(NodeTrace.visibility.in_([NodeTraceVisibility.public, NodeTraceVisibility.system]))
    result = await db.execute(stmt.order_by(NodeTrace.created_at.desc()))
    traces = result.scalars().all()
    return traces

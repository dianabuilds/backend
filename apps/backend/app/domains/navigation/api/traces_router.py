from __future__ import annotations

from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import or_
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

from app.api.deps import get_current_user
from app.core.workspace_context import optional_workspace, require_workspace
from app.domains.navigation.infrastructure.models.transition_models import (
    NodeTrace,
    NodeTraceVisibility,
)
from app.domains.navigation.schemas.traces import NodeTraceCreate, NodeTraceOut
from app.domains.nodes.infrastructure.models.node import Node
from app.domains.users.infrastructure.models.user import User
from app.providers.db.session import get_db

router = APIRouter(prefix="/traces", tags=["traces"])


@router.post("", response_model=NodeTraceOut, summary="Create trace")
async def create_trace(
    payload: NodeTraceCreate,
    current_user: Annotated[User, Depends(get_current_user)] = ...,
    db: Annotated[AsyncSession, Depends(get_db)] = ...,
    _workspace: Annotated[object, Depends(require_workspace)] = ...,
):
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
    node_id: Annotated[UUID, Query(...)] = ...,
    visible_to: Annotated[str, Query(pattern="^(all|me)$")] = "all",
    current_user: Annotated[User, Depends(get_current_user)] = ...,
    db: Annotated[AsyncSession, Depends(get_db)] = ...,
    workspace_dep: Annotated[object, Depends(optional_workspace)] = ...,
):
    stmt = select(NodeTrace).where(NodeTrace.node_id == node_id)
    if visible_to == "me":
        stmt = stmt.where(
            or_(
                NodeTrace.visibility.in_(
                    [NodeTraceVisibility.public, NodeTraceVisibility.system]
                ),
                NodeTrace.user_id == current_user.id,
            )
        )
    else:
        stmt = stmt.where(
            NodeTrace.visibility.in_(
                [NodeTraceVisibility.public, NodeTraceVisibility.system]
            )
        )
    result = await db.execute(stmt.order_by(NodeTrace.created_at.desc()))
    return result.scalars().all()

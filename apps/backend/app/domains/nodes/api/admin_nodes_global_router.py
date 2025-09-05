from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Path
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.domains.nodes.infrastructure.models.node import Node
from app.domains.nodes.infrastructure.repositories.node_repository import (
    NodeRepository,
)
from app.domains.nodes.schemas.node import NodeOut, NodeUpdate
from app.providers.db.session import get_db
from app.security import ADMIN_AUTH_RESPONSES, require_admin_role

router = APIRouter(prefix="/admin/nodes", tags=["admin"], responses=ADMIN_AUTH_RESPONSES)
admin_required = require_admin_role()


@router.get("/{node_id}", response_model=NodeOut, summary="Get global node by ID")
async def get_global_node_by_id(
    node_id: Annotated[int, Path(...)],
    current_user=Depends(admin_required),  # noqa: B008
    db: Annotated[AsyncSession, Depends(get_db)] = ...,  # noqa: B008
) -> NodeOut:
    result = await db.execute(
        select(Node)
        .where(Node.id == node_id, Node.account_id.is_(None))
        .options(selectinload(Node.tags))
    )
    node = result.scalar_one_or_none()
    if not node:
        raise HTTPException(status_code=404, detail="Node not found")
    return NodeOut.model_validate(node)


@router.put("/{node_id}", response_model=NodeOut, summary="Update global node by ID")
async def update_global_node_by_id(
    node_id: Annotated[int, Path(...)],
    payload: NodeUpdate,
    current_user=Depends(admin_required),  # noqa: B008
    db: Annotated[AsyncSession, Depends(get_db)] = ...,  # noqa: B008,
) -> NodeOut:
    repo = NodeRepository(db)
    node = await repo.get_by_id(node_id, None)
    if not node:
        raise HTTPException(status_code=404, detail="Node not found")
    node = await repo.update(node, payload, current_user.id)
    return NodeOut.model_validate(node)

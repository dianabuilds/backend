from __future__ import annotations

from typing import Annotated, List
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user
from app.domains.nodes.infrastructure.repositories.node_repository import NodeRepository
from app.domains.users.infrastructure.models.user import User
from app.providers.db.session import get_db
from app.schemas.node import NodeCreate, NodeOut, NodeUpdate

router = APIRouter(prefix="/users/me/nodes", tags=["nodes"])


@router.get("", response_model=List[NodeOut], summary="List my nodes")
async def list_my_nodes(
    current_user: Annotated[User, Depends(get_current_user)] = ...,
    db: Annotated[AsyncSession, Depends(get_db)] = ...,
) -> List[NodeOut]:
    repo = NodeRepository(db)
    nodes = await repo.list_by_author(current_user.id, limit=100, offset=0)
    return nodes


@router.post("", response_model=NodeOut, status_code=201, summary="Create my node")
async def create_my_node(
    payload: NodeCreate | None = None,
    current_user: Annotated[User, Depends(get_current_user)] = ...,
    db: Annotated[AsyncSession, Depends(get_db)] = ...,
) -> NodeOut:
    repo = NodeRepository(db)
    node = await repo.create_personal(payload or NodeCreate(), current_user.id)
    if not node:
        raise HTTPException(status_code=500, detail="Failed to create node")
    return node


@router.patch("/{node_id}", response_model=NodeOut, summary="Update my node")
async def update_my_node(
    node_id: int,
    patch: NodeUpdate,
    current_user: Annotated[User, Depends(get_current_user)] = ...,
    db: Annotated[AsyncSession, Depends(get_db)] = ...,
) -> NodeOut:
    repo = NodeRepository(db)
    node = await repo.get_by_id_simple(node_id)
    if node is None or node.author_id != current_user.id:
        raise HTTPException(status_code=404, detail="Node not found")
    updated = await repo.update(node, patch, current_user.id)
    return updated


@router.get("/{node_id}", response_model=NodeOut, summary="Get my node")
async def get_my_node(
    node_id: int,
    current_user: Annotated[User, Depends(get_current_user)] = ...,
    db: Annotated[AsyncSession, Depends(get_db)] = ...,
) -> NodeOut:
    repo = NodeRepository(db)
    node = await repo.get_by_id_simple(node_id)
    if node is None or node.author_id != current_user.id:
        raise HTTPException(status_code=404, detail="Node not found")
    return node

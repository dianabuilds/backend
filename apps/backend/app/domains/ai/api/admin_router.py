from __future__ import annotations

from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import assert_owner_or_role
from app.domains.ai.application.embedding_service import update_node_embedding
from app.domains.nodes.infrastructure.models.node import Node
from app.providers.db.session import get_db
from app.security import ADMIN_AUTH_RESPONSES, require_admin_role

router = APIRouter(prefix="/admin/ai", tags=["admin-ai"], responses=ADMIN_AUTH_RESPONSES)
admin_required = require_admin_role()


@router.post("/nodes/{node_id}/embedding/recompute", summary="Recompute node embedding")
async def recompute_node_embedding(
    node_id: UUID,
    current_user=Depends(admin_required),  # noqa: B008
    db: Annotated[AsyncSession, Depends(get_db)] = ...,
):
    node = await db.get(Node, node_id)
    if not node:
        raise HTTPException(status_code=404, detail="Node not found")
    assert_owner_or_role(node.author_id, "moderator", current_user)
    await update_node_embedding(db, node)
    return {"embedding_dim": len(node.embedding_vector or [])}

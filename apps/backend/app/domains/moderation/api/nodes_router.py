from __future__ import annotations

from datetime import datetime
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from app.domains.nodes.infrastructure.repositories.node_repository import (
    NodeRepository,
)
from app.providers.db.session import get_db
from app.security import ADMIN_AUTH_RESPONSES, require_admin_role

admin_required = require_admin_role()

router = APIRouter(
    prefix="/admin/workspaces/{workspace_id}/moderation/nodes",
    tags=["admin"],
    dependencies=[Depends(admin_required)],
    responses=ADMIN_AUTH_RESPONSES,
)


class HidePayload(BaseModel):
    reason: str | None = None


@router.post("/{slug}/hide")
async def hide_node(
    workspace_id: int,
    slug: str,
    payload: HidePayload,
    db: Annotated[AsyncSession, Depends(get_db)] = ...,  # noqa: B008
) -> dict[str, str]:
    repo = NodeRepository(db)
    node = await repo.get_by_slug(slug, workspace_id)
    if not node:
        raise HTTPException(status_code=404, detail="Node not found")
    if node.is_visible:
        node.is_visible = False
        node.updated_at = datetime.utcnow()
        await db.commit()
    return {"status": "ok"}


@router.post("/{slug}/restore")
async def restore_node(
    workspace_id: int,
    slug: str,
    db: Annotated[AsyncSession, Depends(get_db)] = ...,  # noqa: B008
) -> dict[str, str]:
    repo = NodeRepository(db)
    node = await repo.get_by_slug(slug, workspace_id)
    if not node:
        raise HTTPException(status_code=404, detail="Node not found")
    if not node.is_visible:
        node.is_visible = True
        node.updated_at = datetime.utcnow()
        await db.commit()
    return {"status": "ok"}

from __future__ import annotations

from datetime import datetime
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from app.providers.db.session import get_db
from app.security import ADMIN_AUTH_RESPONSES, require_admin_role

admin_required = require_admin_role()

router = APIRouter(
    prefix="/admin/moderation/nodes",
    tags=["admin"],
    dependencies=[Depends(admin_required)],
    responses=ADMIN_AUTH_RESPONSES,
)


class HidePayload(BaseModel):
    reason: str | None = None


@router.post("/{slug}/hide")
async def hide_node(
    slug: str,
    payload: HidePayload,
    db: Annotated[AsyncSession, Depends(get_db)] = ...,  # noqa: B008
) -> dict[str, str]:
    from sqlalchemy import select

    from app.domains.nodes.infrastructure.models.node import Node

    result = await db.execute(select(Node).where(Node.slug == slug))
    node = result.scalar_one_or_none()
    if not node:
        raise HTTPException(status_code=404, detail="Node not found")
    if node.is_visible:
        node.is_visible = False
        node.updated_at = datetime.utcnow()
        await db.commit()
    return {"status": "ok"}


@router.post("/{slug}/restore")
async def restore_node(
    slug: str,
    db: Annotated[AsyncSession, Depends(get_db)] = ...,  # noqa: B008
) -> dict[str, str]:
    from sqlalchemy import select

    from app.domains.nodes.infrastructure.models.node import Node

    result = await db.execute(select(Node).where(Node.slug == slug))
    node = result.scalar_one_or_none()
    if not node:
        raise HTTPException(status_code=404, detail="Node not found")
    if not node.is_visible:
        node.is_visible = True
        node.updated_at = datetime.utcnow()
        await db.commit()
    return {"status": "ok"}

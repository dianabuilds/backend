from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from uuid import UUID

from app.api.deps import get_current_user_optional
from app.db.session import get_db
from app.engine.navigation_engine import get_navigation
from app.engine.compass import get_compass_nodes
from app.models.node import Node
from app.models.user import User

router = APIRouter(prefix="/navigation", tags=["navigation"])


@router.get("/compass")
async def compass_endpoint(
    node_id: UUID,
    user_id: UUID | None = None,
    db: AsyncSession = Depends(get_db),
):
    node = await db.get(Node, node_id)
    if not node or not node.is_visible or not node.is_public or not node.is_recommendable:
        raise HTTPException(status_code=404, detail="Node not found")
    user = None
    if user_id:
        user = await db.get(User, user_id)
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
    nodes = await get_compass_nodes(db, node, user, 5)
    return [
        {
            "id": str(n.id),
            "title": n.title,
            "subtitle": None,
            "tags": n.tag_slugs,
            "hint": None,
        }
        for n in nodes
    ]


@router.get("/{slug}")
async def navigation(
    slug: str,
    db: AsyncSession = Depends(get_db),
    user: User | None = Depends(get_current_user_optional),
):
    result = await db.execute(select(Node).where(Node.slug == slug))
    node = result.scalars().first()
    if not node or not node.is_visible:
        raise HTTPException(status_code=404, detail="Node not found")
    return await get_navigation(db, node, user)

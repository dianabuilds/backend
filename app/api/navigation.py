from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

from app.api.deps import get_current_user_optional
from app.db.session import get_db
from app.engine.navigation_engine import get_navigation
from app.models.node import Node
from app.models.user import User

router = APIRouter(prefix="/navigation", tags=["navigation"])


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

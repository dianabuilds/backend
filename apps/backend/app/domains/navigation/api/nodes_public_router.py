from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

from app.api.deps import get_current_user_optional, get_preview_context
from app.core.db.session import get_db
from app.core.preview import PreviewContext
from app.domains.nodes.infrastructure.models.node import Node
from app.domains.users.infrastructure.models.user import User
from app.domains.navigation.application.navigation_service import NavigationService
from app.domains.navigation.application.modes_service import ModesService
from app.domains.navigation.application.access_policy import has_access_async
from app.schemas.transition import TransitionMode

router = APIRouter(prefix="/nodes", tags=["nodes-navigation"])


@router.get("/{slug}/next", summary="Get next transitions (auto)")
async def get_next_nodes(
    slug: str,
    db: AsyncSession = Depends(get_db),
    user: User | None = Depends(get_current_user_optional),
    preview: PreviewContext = Depends(get_preview_context),
):
    result = await db.execute(select(Node).where(Node.slug == slug))
    node = result.scalars().first()
    if not node or not await has_access_async(node, user, preview):
        raise HTTPException(status_code=404, detail="Node not found")
    return await NavigationService().get_navigation(db, node, user, preview)


@router.get("/{slug}/next_modes", summary="Get next modes options")
async def get_next_modes(
    slug: str,
    db: AsyncSession = Depends(get_db),
    user: User | None = Depends(get_current_user_optional),
):
    result = await db.execute(select(Node).where(Node.slug == slug))
    node = result.scalars().first()
    if not node or not node.is_visible:
        raise HTTPException(status_code=404, detail="Node not found")

    # Пример набора режимов (при реальном переносе возьмём конфиг из node.meta)
    modes = [
        TransitionMode(mode="compass", label="Compass", filters={}),
        TransitionMode(mode="random", label="Random", filters={}),
    ]
    return {
        "default_mode": "compass",
        "modes": [m.model_dump() for m in modes],
    }

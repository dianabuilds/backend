from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

from app.api.deps import get_current_user_optional, get_preview_context
from app.core.preview import PreviewContext
from app.domains.navigation.application.navigation_service import NavigationService
from app.domains.nodes.infrastructure.models.node import Node
from app.domains.users.infrastructure.models.user import User
from app.providers.db.session import get_db
from app.schemas.transition import TransitionMode

router = APIRouter(prefix="/nodes", tags=["nodes-navigation"])


@router.get("/{slug}/next", summary="Get next transitions (auto)")
async def get_next_nodes(
    slug: str,
    db: Annotated[AsyncSession, Depends(get_db)] = ...,
    user: Annotated[User | None, Depends(get_current_user_optional)] = ...,
    preview: Annotated[PreviewContext, Depends(get_preview_context)] = ...,
):
    result = await db.execute(select(Node).where(Node.slug == slug))
    node = result.scalars().first()
    if not node or not node.is_visible or not node.is_public:
        raise HTTPException(status_code=404, detail="Node not found")
    return await NavigationService().get_navigation(db, node, user, preview)


@router.get("/{slug}/next_modes", summary="Get next modes options")
async def get_next_modes(
    slug: str,
    db: Annotated[AsyncSession, Depends(get_db)] = ...,
    user: Annotated[User | None, Depends(get_current_user_optional)] = ...,
):
    result = await db.execute(select(Node).where(Node.slug == slug))
    node = result.scalars().first()
    if not node or not node.is_visible or not node.is_public:
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

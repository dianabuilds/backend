from __future__ import annotations

from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

from app.api.deps import get_current_user_optional, get_preview_context
from app.core.db.session import get_db
from app.core.preview import PreviewContext
from app.domains.navigation.application.compass_service import CompassService
from app.domains.navigation.application.navigation_service import NavigationService
from app.domains.nodes.infrastructure.models.node import Node
from app.domains.telemetry.application.event_metrics_facade import event_metrics
from app.domains.users.infrastructure.models.user import User

router = APIRouter(prefix="/navigation", tags=["navigation"])


@router.get("/compass", summary="Compass recommendations")
async def compass_endpoint(
    node_id: UUID,
    user_id: UUID | None = None,
    db: Annotated[AsyncSession, Depends(get_db)] = ...,
    preview: Annotated[PreviewContext, Depends(get_preview_context)] = ...,
):
    node = await db.get(Node, node_id)
    if (
        not node
        or not node.is_visible
        or not node.is_public
        or not node.is_recommendable
    ):
        raise HTTPException(status_code=404, detail="Node not found")

    user = None
    if user_id:
        user = await db.get(User, user_id)
        if not user:
            raise HTTPException(status_code=404, detail="User not found")

    nodes = await CompassService().get_compass_nodes(db, node, user, 5, preview)
    event_metrics.inc("compass", str(node.workspace_id))
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


@router.get("/{slug}", summary="Navigate from node")
async def navigation(
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

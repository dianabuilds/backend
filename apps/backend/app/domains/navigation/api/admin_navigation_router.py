from __future__ import annotations

from typing import Annotated

# ruff: noqa: B008
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

from app.domains.navigation.application.navigation_cache_service import (
    NavigationCacheService,
)
from app.domains.navigation.application.navigation_service import NavigationService
from app.domains.navigation.application.problems_service import (
    NavigationProblemsService,
)
from app.domains.navigation.infrastructure.cache_adapter import CoreCacheAdapter
from app.domains.navigation.schemas.problems import NavigationNodeProblem
from app.domains.nodes.infrastructure.models.node import Node
from app.domains.users.infrastructure.models.user import User
from app.providers.db.session import get_db
from app.schemas.navigation_admin import (
    NavigationCacheInvalidateRequest,
    NavigationCacheSetRequest,
    NavigationRunRequest,
)
from app.security import ADMIN_AUTH_RESPONSES, require_admin_role

navcache = NavigationCacheService(CoreCacheAdapter())

admin_required = require_admin_role()

router = APIRouter(
    prefix="/admin/navigation",
    tags=["admin"],
    dependencies=[Depends(admin_required)],
    responses=ADMIN_AUTH_RESPONSES,
)


@router.get(
    "/problems",
    response_model=list[NavigationNodeProblem],
    summary="Navigation problems",
)
async def navigation_problems(
    current_user: Annotated[User, Depends(admin_required)] = ...,
    db: Annotated[AsyncSession, Depends(get_db)] = ...,
):
    svc = NavigationProblemsService()
    return await svc.analyse(db)


@router.post("/run", summary="Run navigation generation")
async def run_navigation(
    payload: NavigationRunRequest,
    current_user: Annotated[User, Depends(admin_required)] = ...,
    db: Annotated[AsyncSession, Depends(get_db)] = ...,
):
    node_result = await db.execute(select(Node).where(Node.slug == payload.node_slug))
    node = node_result.scalars().first()
    if not node:
        raise HTTPException(status_code=404, detail="Node not found")
    user: User | None = None
    if payload.user_id:
        user = await db.get(User, payload.user_id)
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
    transitions = await NavigationService().generate_transitions(db, node, user)
    return {"transitions": transitions}


@router.post("/cache/set", summary="Set navigation cache")
async def set_cache(
    payload: NavigationCacheSetRequest,
    current_user: Annotated[User, Depends(admin_required)] = ...,
):
    user_key = str(payload.user_id) if payload.user_id else "anon"
    await navcache.set_navigation(user_key, payload.node_slug, "auto", payload.payload)
    return {"status": "ok"}


@router.post("/cache/invalidate", summary="Invalidate navigation cache")
async def invalidate_cache(
    payload: NavigationCacheInvalidateRequest,
    current_user: Annotated[User, Depends(admin_required)] = ...,
):
    if payload.scope == "node":
        if not payload.node_slug or not payload.account_id:
            raise HTTPException(status_code=400, detail="node_slug and account_id required")
        await navcache.invalidate_navigation_by_node(payload.account_id, payload.node_slug)
    elif payload.scope == "user":
        if not payload.user_id:
            raise HTTPException(status_code=400, detail="user_id required")
        await navcache.invalidate_navigation_by_user(payload.user_id)
    else:
        await navcache.invalidate_navigation_all()
    return {"status": "ok"}


@router.get("/pgvector/status", summary="pgvector status")
async def pgvector_status(
    current_user: Annotated[User, Depends(admin_required)] = ...,  # noqa: B008
    db: Annotated[AsyncSession, Depends(get_db)] = ...,  # noqa: B008
):
    from app.domains.navigation.infrastructure.repositories.compass_repository import (
        CompassRepository,
    )

    repo = CompassRepository(db)
    enabled = repo.session.get_bind().dialect.name == "postgresql"
    return {"enabled": enabled}

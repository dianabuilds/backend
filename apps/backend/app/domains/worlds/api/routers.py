from __future__ import annotations

from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.domains.ai.infrastructure.models.world_models import WorldTemplate
from app.api.deps import get_tenant_id
from app.domains.users.infrastructure.models.user import User
from app.domains.worlds.application.worlds_service import WorldsService
from app.domains.worlds.infrastructure.repositories.worlds_repository import (
    WorldsRepository,
)
from app.providers.db.session import get_db
from app.schemas.worlds import (
    CharacterIn,
    CharacterOut,
    WorldTemplateIn,
    WorldTemplateOut,
)
from app.security import ADMIN_AUTH_RESPONSES, require_admin_role

router = APIRouter(prefix="/admin/worlds", tags=["admin-worlds"], responses=ADMIN_AUTH_RESPONSES)
admin_required = require_admin_role({"admin", "moderator"})


def _svc(db: AsyncSession) -> WorldsService:
    return WorldsService(WorldsRepository(db))


@router.get("", response_model=list[WorldTemplateOut], summary="List world templates")
async def list_worlds(
    tenant: Annotated[UUID, Depends(get_tenant_id)],
    current_user: Annotated[User, Depends(admin_required)] = ...,
    db: Annotated[AsyncSession, Depends(get_db)] = ...,
):
    return await _svc(db).list_worlds(tenant)


@router.post("", response_model=WorldTemplateOut, summary="Create world template")
async def create_world(
    payload: WorldTemplateIn,
    tenant: Annotated[UUID, Depends(get_tenant_id)],
    current_user: Annotated[User, Depends(admin_required)] = ...,
    db: Annotated[AsyncSession, Depends(get_db)] = ...,
):
    return await _svc(db).create_world(
        db, tenant, payload.model_dump(exclude_none=True), current_user.id
    )


@router.patch("/{world_id}", response_model=WorldTemplateOut, summary="Update world template")
async def update_world(
    world_id: UUID,
    payload: WorldTemplateIn,
    tenant: Annotated[UUID, Depends(get_tenant_id)],
    current_user: Annotated[User, Depends(admin_required)] = ...,
    db: Annotated[AsyncSession, Depends(get_db)] = ...,
):
    res = await db.execute(select(WorldTemplate).where(WorldTemplate.id == world_id))
    world = res.scalars().first()
    if not world:
        raise HTTPException(status_code=404, detail="World not found")
    if world.workspace_id != tenant:
        # Cross-tenant access via shared objects is not allowed.
        raise HTTPException(status_code=403, detail="No access")
    out = await _svc(db).update_world(
        db,
        world.workspace_id,
        world_id,
        payload.model_dump(exclude_none=True),
        current_user.id,
    )
    if not out:
        raise HTTPException(status_code=404, detail="World not found")
    return out


@router.delete("/{world_id}", summary="Delete world template")
async def delete_world(
    world_id: UUID,
    tenant: Annotated[UUID, Depends(get_tenant_id)],
    current_user: Annotated[User, Depends(admin_required)] = ...,
    db: Annotated[AsyncSession, Depends(get_db)] = ...,
):
    res = await db.execute(select(WorldTemplate).where(WorldTemplate.id == world_id))
    world = res.scalars().first()
    if not world:
        raise HTTPException(status_code=404, detail="World not found")
    if world.workspace_id != tenant:
        # Cross-tenant access via shared objects is not allowed.
        raise HTTPException(status_code=403, detail="No access")
    ok = await _svc(db).delete_world(db, world.workspace_id, world_id)
    if not ok:
        raise HTTPException(status_code=404, detail="World not found")
    return {"status": "ok"}


@router.get(
    "/{world_id}/characters",
    response_model=list[CharacterOut],
    summary="List characters",
)
async def list_characters(
    world_id: UUID,
    tenant: Annotated[UUID, Depends(get_tenant_id)],
    current_user: Annotated[User, Depends(admin_required)] = ...,
    db: Annotated[AsyncSession, Depends(get_db)] = ...,
):
    return await _svc(db).list_characters(world_id, tenant)


@router.post("/{world_id}/characters", response_model=CharacterOut, summary="Create character")
async def create_character(
    world_id: UUID,
    payload: CharacterIn,
    tenant: Annotated[UUID, Depends(get_tenant_id)],
    current_user: Annotated[User, Depends(admin_required)] = ...,
    db: Annotated[AsyncSession, Depends(get_db)] = ...,
):
    ch = await _svc(db).create_character(
        db,
        world_id,
        tenant,
        payload.model_dump(exclude_none=True),
        current_user.id,
    )
    if not ch:
        raise HTTPException(status_code=404, detail="World not found")
    return ch


@router.patch("/characters/{char_id}", response_model=CharacterOut, summary="Update character")
async def update_character(
    char_id: UUID,
    payload: CharacterIn,
    tenant: Annotated[UUID, Depends(get_tenant_id)],
    current_user: Annotated[User, Depends(admin_required)] = ...,
    db: Annotated[AsyncSession, Depends(get_db)] = ...,
):
    ch = await _svc(db).update_character(
        db,
        char_id,
        tenant,
        payload.model_dump(exclude_none=True),
        current_user.id,
    )
    if not ch:
        raise HTTPException(status_code=404, detail="Character not found")
    return ch


@router.delete("/characters/{char_id}", summary="Delete character")
async def delete_character(
    char_id: UUID,
    tenant: Annotated[UUID, Depends(get_tenant_id)],
    current_user: Annotated[User, Depends(admin_required)] = ...,
    db: Annotated[AsyncSession, Depends(get_db)] = ...,
):
    ok = await _svc(db).delete_character(db, char_id, tenant)
    if not ok:
        raise HTTPException(status_code=404, detail="Character not found")
    return {"status": "ok"}

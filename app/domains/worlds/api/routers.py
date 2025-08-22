from __future__ import annotations

from typing import Any, Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.db.session import get_db
from app.domains.worlds.application.worlds_service import WorldsService
from app.domains.worlds.infrastructure.repositories.worlds_repository import WorldsRepository
from app.schemas.worlds import WorldTemplateIn, WorldTemplateOut, CharacterIn, CharacterOut
from app.security import ADMIN_AUTH_RESPONSES, require_admin_role
from app.domains.users.infrastructure.models.user import User

router = APIRouter(prefix="/admin/worlds", tags=["admin-worlds"], responses=ADMIN_AUTH_RESPONSES)
admin_required = require_admin_role({"admin", "moderator"})


def _svc(db: AsyncSession) -> WorldsService:
    return WorldsService(WorldsRepository(db))


@router.get("", response_model=list[WorldTemplateOut], summary="List world templates")
async def list_worlds(
    current_user: User = Depends(admin_required),
    db: AsyncSession = Depends(get_db),
):
    return await _svc(db).list_worlds()


@router.post("", response_model=WorldTemplateOut, summary="Create world template")
async def create_world(
    payload: WorldTemplateIn,
    current_user: User = Depends(admin_required),
    db: AsyncSession = Depends(get_db),
):
    return await _svc(db).create_world(db, payload.model_dump(exclude_none=True))


@router.patch("/{world_id}", response_model=WorldTemplateOut, summary="Update world template")
async def update_world(
    world_id: UUID,
    payload: WorldTemplateIn,
    current_user: User = Depends(admin_required),
    db: AsyncSession = Depends(get_db),
):
    out = await _svc(db).update_world(db, world_id, payload.model_dump(exclude_none=True))
    if not out:
        raise HTTPException(status_code=404, detail="World not found")
    return out


@router.delete("/{world_id}", summary="Delete world template")
async def delete_world(
    world_id: UUID,
    current_user: User = Depends(admin_required),
    db: AsyncSession = Depends(get_db),
):
    ok = await _svc(db).delete_world(db, world_id)
    if not ok:
        raise HTTPException(status_code=404, detail="World not found")
    return {"status": "ok"}


@router.get("/{world_id}/characters", response_model=list[CharacterOut], summary="List characters")
async def list_characters(
    world_id: UUID,
    current_user: User = Depends(admin_required),
    db: AsyncSession = Depends(get_db),
):
    return await _svc(db).list_characters(world_id)


@router.post("/{world_id}/characters", response_model=CharacterOut, summary="Create character")
async def create_character(
    world_id: UUID,
    payload: CharacterIn,
    current_user: User = Depends(admin_required),
    db: AsyncSession = Depends(get_db),
):
    ch = await _svc(db).create_character(db, world_id, payload.model_dump(exclude_none=True))
    if not ch:
        raise HTTPException(status_code=404, detail="World not found")
    return ch


@router.patch("/characters/{char_id}", response_model=CharacterOut, summary="Update character")
async def update_character(
    char_id: UUID,
    payload: CharacterIn,
    current_user: User = Depends(admin_required),
    db: AsyncSession = Depends(get_db),
):
    ch = await _svc(db).update_character(db, char_id, payload.model_dump(exclude_none=True))
    if not ch:
        raise HTTPException(status_code=404, detail="Character not found")
    return ch


@router.delete("/characters/{char_id}", summary="Delete character")
async def delete_character(
    char_id: UUID,
    current_user: User = Depends(admin_required),
    db: AsyncSession = Depends(get_db),
):
    ok = await _svc(db).delete_character(db, char_id)
    if not ok:
        raise HTTPException(status_code=404, detail="Character not found")
    return {"status": "ok"}

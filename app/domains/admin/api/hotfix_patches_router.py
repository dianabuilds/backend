from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.db.session import get_db
from app.schemas.content_patch import ContentPatchCreate, ContentPatchOut
from app.security import ADMIN_AUTH_RESPONSES, require_admin_role
from app.domains.content.dao import ContentPatchDAO

admin_only = require_admin_role({"admin"})

router = APIRouter(
    prefix="/admin/hotfix/patches",
    tags=["admin"],
    responses=ADMIN_AUTH_RESPONSES,
)


@router.post("", response_model=ContentPatchOut, summary="Create content patch")
async def create_patch(
    body: ContentPatchCreate,
    current=Depends(admin_only),
    db: AsyncSession = Depends(get_db),
) -> ContentPatchOut:
    patch = await ContentPatchDAO.create(
        db,
        content_id=body.content_id,
        data=body.data,
        created_by_user_id=getattr(current, "id", None),
    )
    await db.commit()
    return patch


@router.post("/{patch_id}/revert", response_model=ContentPatchOut, summary="Revert patch")
async def revert_patch(
    patch_id: UUID,
    current=Depends(admin_only),
    db: AsyncSession = Depends(get_db),
) -> ContentPatchOut:
    patch = await ContentPatchDAO.revert(db, patch_id=patch_id)
    if not patch:
        raise HTTPException(status_code=404, detail="Patch not found")
    await db.commit()
    return patch

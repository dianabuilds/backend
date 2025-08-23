from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.db.session import get_db
from app.domains.nodes.dao import NodePatchDAO
from app.domains.users.infrastructure.models.user import User
from app.schemas.node_patch import NodePatchCreate, NodePatchOut
from app.security import ADMIN_AUTH_RESPONSES, require_admin_role

admin_only = require_admin_role({"admin"})

router = APIRouter(
    prefix="/admin/hotfix/patches",
    tags=["admin"],
    responses=ADMIN_AUTH_RESPONSES,
)


@router.post("", response_model=NodePatchOut, summary="Create node patch")
async def create_patch(
    body: NodePatchCreate,
    current_user: User = Depends(admin_only),  # noqa: B008
    db: AsyncSession = Depends(get_db),  # noqa: B008
) -> NodePatchOut:
    patch = await NodePatchDAO.create(
        db,
        node_id=body.node_id,
        data=body.data,
        created_by_user_id=getattr(current_user, "id", None),
    )
    await db.commit()
    return patch


@router.post("/{patch_id}/revert", response_model=NodePatchOut, summary="Revert patch")
async def revert_patch(
    patch_id: UUID,
    current_user: User = Depends(admin_only),  # noqa: B008
    db: AsyncSession = Depends(get_db),  # noqa: B008
) -> NodePatchOut:
    patch = await NodePatchDAO.revert(db, patch_id=patch_id)
    if not patch:
        raise HTTPException(status_code=404, detail="Patch not found")
    await db.commit()
    return patch

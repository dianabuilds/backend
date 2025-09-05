from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.domains.nodes.dao import NodePatchDAO
from app.domains.users.infrastructure.models.user import User
from app.providers.db.session import get_db
from app.schemas.node_patch import (
    NodePatchCreate,
    NodePatchDiffOut,
    NodePatchOut,
)
from app.security import ADMIN_AUTH_RESPONSES, require_admin_role

admin_only = require_admin_role({"admin"})

router = APIRouter(
    prefix="/admin/hotfix/patches",
    tags=["admin"],
    responses=ADMIN_AUTH_RESPONSES,
)


@router.get("", response_model=list[NodePatchDiffOut], summary="List node patches")
async def list_patches(
    node_id: int | None = None,
    current_user: Annotated[User, Depends(admin_only)] = ...,  # noqa: B008
    db: Annotated[AsyncSession, Depends(get_db)] = ...,  # noqa: B008
) -> list[NodePatchDiffOut]:
    patches = await NodePatchDAO.list(db, node_id=node_id)
    out: list[NodePatchDiffOut] = []
    for patch in patches:
        diff = await NodePatchDAO.diff(db, patch)
        item = NodePatchDiffOut.from_orm(patch)
        item.diff = diff
        out.append(item)
    return out


@router.post("", response_model=NodePatchOut, summary="Create node patch")
async def create_patch(
    body: NodePatchCreate,
    current_user: Annotated[User, Depends(admin_only)] = ...,  # noqa: B008
    db: Annotated[AsyncSession, Depends(get_db)] = ...,  # noqa: B008
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
    patch_id: int,
    current_user: Annotated[User, Depends(admin_only)] = ...,  # noqa: B008
    db: Annotated[AsyncSession, Depends(get_db)] = ...,  # noqa: B008
) -> NodePatchOut:
    patch = await NodePatchDAO.revert(db, patch_id=patch_id)
    if not patch:
        raise HTTPException(status_code=404, detail="Patch not found")
    await db.commit()
    return patch


@router.get("/{patch_id}", response_model=NodePatchDiffOut, summary="Get patch")
async def get_patch(
    patch_id: int,
    current_user: Annotated[User, Depends(admin_only)] = ...,  # noqa: B008
    db: Annotated[AsyncSession, Depends(get_db)] = ...,  # noqa: B008
) -> NodePatchDiffOut:
    patch = await NodePatchDAO.get(db, patch_id=patch_id)
    if not patch:
        raise HTTPException(status_code=404, detail="Patch not found")
    diff = await NodePatchDAO.diff(db, patch)
    out = NodePatchDiffOut.from_orm(patch)
    out.diff = diff
    return out

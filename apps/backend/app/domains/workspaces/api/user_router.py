from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user
from app.domains.users.infrastructure.models.user import User
from app.providers.db.session import get_db
from app.schemas.workspaces import WorkspaceOut

from ..application.service import WorkspaceService

router = APIRouter(prefix="/workspaces", tags=["workspaces"])


@router.get("/", response_model=list[WorkspaceOut], summary="List workspaces")
async def list_workspaces(
    current_user: Annotated[User, Depends(get_current_user)] = ...,
    db: Annotated[AsyncSession, Depends(get_db)] = ...,
) -> list[WorkspaceOut]:
    rows = await WorkspaceService.list_for_user(db, current_user)
    return [
        WorkspaceOut.model_validate(ws, from_attributes=True).model_copy(update={"role": role})
        for ws, role in rows
    ]

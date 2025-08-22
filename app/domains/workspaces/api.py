from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

from app.core.db.session import get_db
from app.security import ADMIN_AUTH_RESPONSES, auth_user, require_ws_editor
from .infrastructure.models import Workspace

router = APIRouter(
    prefix="/admin/workspaces",
    tags=["admin"],
    responses=ADMIN_AUTH_RESPONSES,
)


@router.get("/", summary="List workspaces")
async def list_workspaces(
    _: object = Depends(auth_user),
    db: AsyncSession = Depends(get_db),
) -> dict:
    result = await db.execute(select(Workspace))
    items = result.scalars().all()
    return {
        "workspaces": [{"id": str(ws.id), "name": ws.name} for ws in items]
    }


@router.post("/{workspace_id}", summary="Create workspace")
async def create_workspace(
    workspace_id: UUID,
    _: object = Depends(require_ws_editor),
) -> dict:
    return {"workspace_id": str(workspace_id), "action": "create"}


@router.get("/{workspace_id}", summary="Get workspace")
async def get_workspace(
    workspace_id: UUID,
    _: object = Depends(require_ws_editor),
) -> dict:
    return {"workspace_id": str(workspace_id)}


@router.patch("/{workspace_id}", summary="Update workspace")
async def update_workspace(
    workspace_id: UUID,
    _: object = Depends(require_ws_editor),
) -> dict:
    return {"workspace_id": str(workspace_id), "action": "update"}


@router.delete("/{workspace_id}", summary="Delete workspace")
async def delete_workspace(
    workspace_id: UUID,
    _: object = Depends(require_ws_editor),
) -> dict:
    return {"workspace_id": str(workspace_id), "status": "deleted"}

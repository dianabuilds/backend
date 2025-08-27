from __future__ import annotations

from uuid import UUID
from typing import Optional

from fastapi import Request, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.db.session import get_db
from app.security import auth_user
from app.domains.users.infrastructure.models.user import User
from app.domains.workspaces.infrastructure.dao import WorkspaceDAO, WorkspaceMemberDAO
from app.domains.workspaces.infrastructure.models import Workspace


def get_workspace_id(request: Request) -> Optional[UUID]:
    """Extract workspace identifier from request headers or query params."""
    wid = request.headers.get("X-Workspace-Id") or request.query_params.get("workspace_id")
    if not wid:
        return None
    try:
        return UUID(str(wid))
    except (TypeError, ValueError) as exc:
        raise HTTPException(status_code=400, detail="Invalid workspace id") from exc


async def resolve_workspace(
    workspace_id: UUID, user: User, db: AsyncSession
) -> Workspace:
    """Load workspace and ensure the user is a member or admin."""
    workspace = await WorkspaceDAO.get(db, workspace_id)
    if not workspace:
        raise HTTPException(status_code=404, detail="Workspace not found")
    if user.role != "admin":
        member = await WorkspaceMemberDAO.get(
            db, workspace_id=workspace_id, user_id=user.id
        )
        if not member:
            raise HTTPException(status_code=404, detail="Workspace not found")
    return workspace


async def require_workspace(
    request: Request,
    user: User = Depends(auth_user),
    db: AsyncSession = Depends(get_db),
) -> Workspace:
    workspace_id = get_workspace_id(request)
    if workspace_id is None:
        raise HTTPException(status_code=400, detail="workspace_id required")
    workspace = await resolve_workspace(workspace_id, user, db)
    request.state.workspace_id = str(workspace_id)
    request.state.workspace = workspace
    return workspace


async def optional_workspace(
    request: Request,
    user: User = Depends(auth_user),
    db: AsyncSession = Depends(get_db),
) -> Optional[Workspace]:
    workspace_id = get_workspace_id(request)
    if workspace_id is None:
        return None
    workspace = await resolve_workspace(workspace_id, user, db)
    request.state.workspace_id = str(workspace_id)
    request.state.workspace = workspace
    return workspace


__all__ = [
    "get_workspace_id",
    "resolve_workspace",
    "require_workspace",
    "optional_workspace",
]

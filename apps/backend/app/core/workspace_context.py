from __future__ import annotations

from uuid import UUID

from fastapi import Depends, Header, HTTPException, Request
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.db.session import get_db
from app.domains.users.infrastructure.models.user import User
from app.domains.workspaces.infrastructure.dao import WorkspaceDAO, WorkspaceMemberDAO
from app.domains.workspaces.infrastructure.models import Workspace
from app.security import auth_user


def get_workspace_id(
    request: Request, header_wid: UUID | str | None = None
) -> UUID | None:
    """Extract workspace identifier from path params, headers or query params."""
    if not isinstance(header_wid, (str, UUID, type(None))):
        header_wid = None
    wid = (
        request.path_params.get("workspace_id")
        or header_wid
        or request.headers.get("X-Workspace-Id")
        or request.query_params.get("workspace_id")
    )
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
    workspace_header: UUID | None = Header(
        None, alias="X-Workspace-Id", deprecated=True
    ),
    user: User = Depends(auth_user),
    db: AsyncSession = Depends(get_db),
) -> Workspace:
    workspace_id = get_workspace_id(request, workspace_header)
    if workspace_id is None:
        raise HTTPException(status_code=400, detail="workspace_id required")
    workspace = await resolve_workspace(workspace_id, user, db)
    request.state.workspace_id = str(workspace_id)
    request.state.workspace = workspace
    return workspace


async def optional_workspace(
    request: Request,
    workspace_header: UUID | None = Header(
        None, alias="X-Workspace-Id", deprecated=True
    ),
    user: User = Depends(auth_user),
    db: AsyncSession = Depends(get_db),
) -> Workspace | None:
    workspace_id = get_workspace_id(request, workspace_header)
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

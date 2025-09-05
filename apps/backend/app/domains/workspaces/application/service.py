from __future__ import annotations

from typing import Annotated
from uuid import UUID

from fastapi import Depends, HTTPException, Request, Security
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.ext.asyncio import AsyncSession

from app.domains.accounts.application.service import AccountService
from app.domains.users.infrastructure.models.user import User
from app.providers.db.session import get_db
from app.schemas.workspaces import WorkspaceIn, WorkspaceRole, WorkspaceSettings

from ..infrastructure.dao import WorkspaceDAO, WorkspaceMemberDAO
from ..infrastructure.models import Workspace, WorkspaceMember

bearer_scheme = HTTPBearer(auto_error=False, scheme_name="bearerAuth")


async def _auth_user(
    request: Request,
    credentials: Annotated[
        HTTPAuthorizationCredentials | None, Security(bearer_scheme)  # noqa: B008
    ] = ...,
    db: Annotated[AsyncSession, Depends(get_db)] = ...,  # noqa: B008
) -> User:
    from app.security import auth_user

    return await auth_user(request, credentials, db)


async def require_ws_editor(
    workspace_id: UUID,
    user: Annotated[User, Depends(_auth_user)] = ...,
    db: Annotated[AsyncSession, Depends(get_db)] = ...,
) -> WorkspaceMember | None:
    m = await WorkspaceMemberDAO.get(db, workspace_id=workspace_id, user_id=user.id)
    if not (user.role == "admin" or (m and m.role in (WorkspaceRole.owner, WorkspaceRole.editor))):
        raise HTTPException(status_code=403, detail="Forbidden")
    return m


async def require_ws_owner(
    workspace_id: UUID,
    user: Annotated[User, Depends(_auth_user)] = ...,
    db: Annotated[AsyncSession, Depends(get_db)] = ...,
) -> WorkspaceMember | None:
    m = await WorkspaceMemberDAO.get(db, workspace_id=workspace_id, user_id=user.id)
    if not (user.role == "admin" or (m and m.role == WorkspaceRole.owner)):
        raise HTTPException(status_code=403, detail="Forbidden")
    return m


async def require_ws_viewer(
    workspace_id: UUID,
    user: Annotated[User, Depends(_auth_user)] = ...,
    db: Annotated[AsyncSession, Depends(get_db)] = ...,
) -> WorkspaceMember | None:
    m = await WorkspaceMemberDAO.get(db, workspace_id=workspace_id, user_id=user.id)
    if not (
        user.role == "admin"
        or (m and m.role in (WorkspaceRole.owner, WorkspaceRole.editor, WorkspaceRole.viewer))
    ):
        raise HTTPException(status_code=403, detail="Forbidden")
    return m


async def require_ws_guest(
    workspace_id: UUID,
    user: Annotated[User, Depends(_auth_user)] = ...,
    db: Annotated[AsyncSession, Depends(get_db)] = ...,
) -> WorkspaceMember | None:
    m = await WorkspaceMemberDAO.get(db, workspace_id=workspace_id, user_id=user.id)
    if not (user.role == "admin" or m):
        raise HTTPException(status_code=403, detail="Forbidden")
    return m


class WorkspaceService:
    @staticmethod
    async def create(db: AsyncSession, *, data: WorkspaceIn, owner: User) -> Workspace:
        account = await AccountService.create(db, data=data, owner=owner)
        ws = await WorkspaceDAO.get(db, account.id)
        if not ws:
            raise HTTPException(status_code=500, detail="Workspace not created")
        return ws

    @staticmethod
    async def get_for_user(db: AsyncSession, workspace_id: UUID, user: User) -> Workspace:
        ws = await WorkspaceDAO.get(db, workspace_id)
        if not ws:
            raise HTTPException(status_code=404, detail="Workspace not found")
        if user.role != "admin":
            member = await WorkspaceMemberDAO.get(db, workspace_id=workspace_id, user_id=user.id)
            if not member:
                raise HTTPException(status_code=404, detail="Workspace not found")
        return ws

    @staticmethod
    async def list_for_user(db: AsyncSession, user: User) -> list[tuple[Workspace, WorkspaceRole]]:
        workspaces = await WorkspaceDAO.list_for_user(db, user.id)
        rows: list[tuple[Workspace, WorkspaceRole]] = []
        for ws in workspaces:
            member = await WorkspaceMemberDAO.get(db, workspace_id=ws.id, user_id=user.id)
            role = member.role if member else WorkspaceRole.viewer
            rows.append((ws, role))
        return rows

    @staticmethod
    async def get_ai_presets(db: AsyncSession, workspace_id: UUID) -> dict[str, object]:
        ws = await WorkspaceDAO.get(db, workspace_id)
        if not ws:
            raise HTTPException(status_code=404, detail="Workspace not found")
        settings = WorkspaceSettings.model_validate(ws.settings_json or {})
        return settings.ai_presets


__all__ = [
    "WorkspaceService",
    "require_ws_editor",
    "require_ws_owner",
    "require_ws_viewer",
    "require_ws_guest",
]

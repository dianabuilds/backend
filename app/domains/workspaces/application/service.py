from __future__ import annotations

from uuid import UUID

from fastapi import HTTPException, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.sql import Select

from app.security import auth_user
from app.core.db.session import get_db

from app.schemas.workspaces import (
    WorkspaceIn,
    WorkspaceUpdate,
    WorkspaceMemberIn,
    WorkspaceRole,
)
from app.domains.workspaces.infrastructure.models import Workspace, WorkspaceMember
from app.domains.workspaces.infrastructure.dao import WorkspaceMemberDAO
from app.domains.users.infrastructure.models.user import User


async def require_ws_editor(
    workspace_id: UUID,
    user: User = Depends(auth_user),
    db: AsyncSession = Depends(get_db),
) -> WorkspaceMember | None:
    """Ensure the current user has editor or owner rights in the workspace."""
    m = await WorkspaceMemberDAO.get(
        db, workspace_id=workspace_id, user_id=user.id
    )
    if not (
        user.role == "admin"
        or (m and m.role in (WorkspaceRole.owner, WorkspaceRole.editor))
    ):
        raise HTTPException(status_code=403, detail="Forbidden")
    return m


async def require_ws_owner(
    workspace_id: UUID,
    user: User = Depends(auth_user),
    db: AsyncSession = Depends(get_db),
) -> WorkspaceMember | None:
    """Ensure the current user is an owner of the workspace."""
    m = await WorkspaceMemberDAO.get(
        db, workspace_id=workspace_id, user_id=user.id
    )
    if not (user.role == "admin" or (m and m.role == WorkspaceRole.owner)):
        raise HTTPException(status_code=403, detail="Forbidden")
    return m


def scope_by_workspace(query: Select, workspace_id: UUID) -> Select:
    """Filter a SQLAlchemy query by workspace identifier if possible."""
    entity = query.column_descriptions[0]["entity"]
    if hasattr(entity, "workspace_id"):
        query = query.where(entity.workspace_id == workspace_id)
    return query


class WorkspaceService:
    @staticmethod
    async def create(db: AsyncSession, *, data: WorkspaceIn, owner: User) -> Workspace:
        workspace = Workspace(
            name=data.name,
            slug=data.slug or data.name,
            owner_user_id=owner.id,
            settings_json=data.settings,
        )
        db.add(workspace)
        db.add(
            WorkspaceMember(
                workspace=workspace, user_id=owner.id, role=WorkspaceRole.owner
            )
        )
        await db.commit()
        await db.refresh(workspace)
        return workspace

    @staticmethod
    async def get_for_user(
        db: AsyncSession, workspace_id: UUID, user: User
    ) -> Workspace:
        workspace = await db.get(Workspace, workspace_id)
        if not workspace:
            raise HTTPException(status_code=404, detail="Workspace not found")
        if user.role != "admin":
            member = await WorkspaceMemberDAO.get(
                db, workspace_id=workspace_id, user_id=user.id
            )
            if not member:
                raise HTTPException(status_code=404, detail="Workspace not found")
        return workspace

    @staticmethod
    async def update(
        db: AsyncSession, workspace_id: UUID, data: WorkspaceUpdate
    ) -> Workspace:
        workspace = await db.get(Workspace, workspace_id)
        if not workspace:
            raise HTTPException(status_code=404, detail="Workspace not found")
        if data.name is not None:
            workspace.name = data.name
        if data.slug is not None:
            workspace.slug = data.slug
        if data.settings is not None:
            workspace.settings_json = data.settings
        await db.commit()
        await db.refresh(workspace)
        return workspace

    @staticmethod
    async def delete(db: AsyncSession, workspace_id: UUID) -> None:
        workspace = await db.get(Workspace, workspace_id)
        if not workspace:
            raise HTTPException(status_code=404, detail="Workspace not found")
        await db.delete(workspace)
        await db.commit()

    @staticmethod
    async def add_member(
        db: AsyncSession, workspace_id: UUID, data: WorkspaceMemberIn
    ) -> WorkspaceMember:
        existing = await WorkspaceMemberDAO.get(
            db, workspace_id=workspace_id, user_id=data.user_id
        )
        if existing:
            raise HTTPException(status_code=400, detail="Member already exists")
        member = WorkspaceMember(
            workspace_id=workspace_id,
            user_id=data.user_id,
            role=data.role,
        )
        db.add(member)
        await db.commit()
        await db.refresh(member)
        return member

    @staticmethod
    async def update_member(
        db: AsyncSession, workspace_id: UUID, user_id: UUID, role: WorkspaceRole
    ) -> WorkspaceMember:
        member = await WorkspaceMemberDAO.get(
            db, workspace_id=workspace_id, user_id=user_id
        )
        if not member:
            raise HTTPException(status_code=404, detail="Member not found")
        member.role = role
        await db.commit()
        await db.refresh(member)
        return member

    @staticmethod
    async def remove_member(
        db: AsyncSession, workspace_id: UUID, user_id: UUID
    ) -> None:
        member = await WorkspaceMemberDAO.get(
            db, workspace_id=workspace_id, user_id=user_id
        )
        if not member:
            raise HTTPException(status_code=404, detail="Member not found")
        await db.delete(member)
        await db.commit()

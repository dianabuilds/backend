from __future__ import annotations

from uuid import UUID

from fastapi import HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.schemas.workspaces import (
    WorkspaceIn,
    WorkspaceUpdate,
    WorkspaceMemberIn,
)
from app.domains.workspaces.infrastructure.models import Workspace, WorkspaceMember
from app.domains.workspaces.infrastructure.dao import WorkspaceMemberDAO
from app.domains.users.infrastructure.models.user import User


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
                workspace=workspace, user_id=owner.id, role="owner"
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
    def ensure_owner(user: User, member: WorkspaceMember | None) -> None:
        if user.role != "admin" and (
            member is None or member.role != "owner"
        ):
            raise HTTPException(status_code=403, detail="Forbidden")

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
        db: AsyncSession, workspace_id: UUID, user_id: UUID, role: str
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

from __future__ import annotations

import re
from uuid import UUID

from fastapi import Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.sql import Select

from app.core.db.session import get_db
from app.domains.users.infrastructure.models.user import User
from app.domains.workspaces.infrastructure.dao import WorkspaceDAO, WorkspaceMemberDAO
from app.domains.workspaces.infrastructure.models import Workspace, WorkspaceMember
from app.schemas.workspaces import (
    WorkspaceIn,
    WorkspaceMemberIn,
    WorkspaceRole,
    WorkspaceUpdate,
)
from app.security import auth_user


async def require_ws_editor(
    workspace_id: UUID,
    user: User = Depends(auth_user),
    db: AsyncSession = Depends(get_db),
) -> WorkspaceMember | None:
    """Ensure the current user has editor or owner rights in the workspace."""
    m = await WorkspaceMemberDAO.get(db, workspace_id=workspace_id, user_id=user.id)
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
    m = await WorkspaceMemberDAO.get(db, workspace_id=workspace_id, user_id=user.id)
    if not (user.role == "admin" or (m and m.role == WorkspaceRole.owner)):
        raise HTTPException(status_code=403, detail="Forbidden")
    return m


async def require_ws_viewer(
    workspace_id: UUID,
    user: User = Depends(auth_user),
    db: AsyncSession = Depends(get_db),
) -> WorkspaceMember | None:
    """Ensure the current user has at least viewer rights in the workspace."""
    m = await WorkspaceMemberDAO.get(db, workspace_id=workspace_id, user_id=user.id)
    if not (
        user.role == "admin"
        or (
            m
            and m.role
            in (WorkspaceRole.owner, WorkspaceRole.editor, WorkspaceRole.viewer)
        )
    ):
        raise HTTPException(status_code=403, detail="Forbidden")
    return m


async def require_ws_guest(
    workspace_id: UUID,
    user: User = Depends(auth_user),
    db: AsyncSession = Depends(get_db),
) -> WorkspaceMember | None:
    """Ensure the current user is a member of the workspace."""
    m = await WorkspaceMemberDAO.get(db, workspace_id=workspace_id, user_id=user.id)
    if not (user.role == "admin" or m):
        raise HTTPException(status_code=403, detail="Forbidden")
    return m


def scope_by_workspace(query: Select, workspace_id: UUID) -> Select:
    """Filter a SQLAlchemy query by workspace identifier if possible."""
    entity = query.column_descriptions[0]["entity"]
    if hasattr(entity, "workspace_id"):
        query = query.where(entity.workspace_id == workspace_id)
    return query


SLUG_RE = re.compile(r"^[a-z0-9-]+$")


def _slugify(text: str) -> str:
    slug = re.sub(r"[^a-z0-9-]+", "-", text.lower())
    return re.sub(r"-+", "-", slug).strip("-")


class WorkspaceService:
    @staticmethod
    async def create(db: AsyncSession, *, data: WorkspaceIn, owner: User) -> Workspace:
        slug = data.slug or _slugify(data.name)
        if not SLUG_RE.fullmatch(slug):
            raise HTTPException(status_code=400, detail="Invalid slug")
        res = await db.execute(select(Workspace).where(Workspace.slug == slug))
        if res.scalars().first():
            raise HTTPException(status_code=400, detail="Slug already exists")
        res = await db.execute(
            select(Workspace).where(
                Workspace.owner_user_id == owner.id, Workspace.name == data.name
            )
        )
        if res.scalars().first():
            raise HTTPException(status_code=400, detail="Name already exists")
        workspace = Workspace(
            name=data.name,
            slug=slug,
            owner_user_id=owner.id,
            settings_json=data.settings.model_dump(),
            type=data.type,
            is_system=data.is_system,
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

    @staticmethod
    async def update(
        db: AsyncSession, workspace_id: UUID, data: WorkspaceUpdate
    ) -> Workspace:
        workspace = await WorkspaceDAO.get(db, workspace_id)
        if not workspace:
            raise HTTPException(status_code=404, detail="Workspace not found")
        if data.name is not None and data.name != workspace.name:
            res = await db.execute(
                select(Workspace).where(
                    Workspace.owner_user_id == workspace.owner_user_id,
                    Workspace.name == data.name,
                    Workspace.id != workspace_id,
                )
            )
            if res.scalars().first():
                raise HTTPException(status_code=400, detail="Name already exists")
            workspace.name = data.name
        if data.slug is not None and data.slug != workspace.slug:
            if not SLUG_RE.fullmatch(data.slug):
                raise HTTPException(status_code=400, detail="Invalid slug")
            res = await db.execute(
                select(Workspace).where(
                    Workspace.slug == data.slug, Workspace.id != workspace_id
                )
            )
            if res.scalars().first():
                raise HTTPException(status_code=400, detail="Slug already exists")
            workspace.slug = data.slug
        if data.settings is not None:
            workspace.settings_json = data.settings.model_dump()
        if data.type is not None:
            workspace.type = data.type
        if data.is_system is not None:
            workspace.is_system = data.is_system
        await db.commit()
        await db.refresh(workspace)
        return workspace

    @staticmethod
    async def delete(db: AsyncSession, workspace_id: UUID) -> None:
        workspace = await WorkspaceDAO.get(db, workspace_id)
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
        member = await WorkspaceMemberDAO.add(
            db,
            workspace_id=workspace_id,
            user_id=data.user_id,
            role=data.role,
        )
        await db.commit()
        await db.refresh(member)
        return member

    @staticmethod
    async def update_member(
        db: AsyncSession, workspace_id: UUID, user_id: UUID, role: WorkspaceRole
    ) -> WorkspaceMember:
        member = await WorkspaceMemberDAO.update_role(
            db, workspace_id=workspace_id, user_id=user_id, role=role
        )
        if not member:
            raise HTTPException(status_code=404, detail="Member not found")
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
        await WorkspaceMemberDAO.remove(db, workspace_id=workspace_id, user_id=user_id)
        await db.commit()

    @staticmethod
    async def list_members(
        db: AsyncSession, workspace_id: UUID
    ) -> list[WorkspaceMember]:
        res = await db.execute(
            select(WorkspaceMember).where(WorkspaceMember.workspace_id == workspace_id)
        )
        return res.scalars().all()

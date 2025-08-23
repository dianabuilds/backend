from __future__ import annotations

from datetime import datetime, timezone
from uuid import UUID
from typing import List
import logging

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

from app.schemas.workspaces import WorkspaceRole, WorkspaceSettings

from .models import Workspace, WorkspaceMember


logger = logging.getLogger("app.audit.workspace_member")


class WorkspaceDAO:
    """Data access helpers for :class:`Workspace` objects."""

    @staticmethod
    async def create(
        db: AsyncSession,
        *,
        name: str,
        slug: str,
        owner_user_id: UUID,
        settings: WorkspaceSettings | None = None,
    ) -> Workspace:
        workspace = Workspace(
            name=name,
            slug=slug,
            owner_user_id=owner_user_id,
            settings_json=settings.model_dump() if settings else {},
        )
        db.add(workspace)
        await db.flush()
        return workspace

    @staticmethod
    async def get(db: AsyncSession, workspace_id: UUID) -> Workspace | None:
        return await db.get(Workspace, workspace_id)

    @staticmethod
    async def list_for_user(db: AsyncSession, user_id: UUID) -> List[Workspace]:
        stmt = (
            select(Workspace)
            .join(WorkspaceMember)
            .where(WorkspaceMember.user_id == user_id)
            .order_by(Workspace.name)
        )
        result = await db.execute(stmt)
        return list(result.scalars().all())

    @staticmethod
    async def update(
        db: AsyncSession,
        workspace: Workspace,
        *,
        name: str | None = None,
        slug: str | None = None,
        settings: WorkspaceSettings | None = None,
    ) -> Workspace:
        if name is not None:
            workspace.name = name
        if slug is not None:
            workspace.slug = slug
        if settings is not None:
            workspace.settings_json = settings.model_dump()
        await db.flush()
        return workspace

    @staticmethod
    async def delete(db: AsyncSession, workspace: Workspace) -> None:
        await db.delete(workspace)
        await db.flush()


class WorkspaceMemberDAO:
    @staticmethod
    async def get(
        db: AsyncSession, *, workspace_id: UUID, user_id: UUID
    ) -> WorkspaceMember | None:
        stmt = select(WorkspaceMember).where(
            WorkspaceMember.workspace_id == workspace_id,
            WorkspaceMember.user_id == user_id,
        )
        result = await db.execute(stmt)
        return result.scalars().first()

    @staticmethod
    async def add(
        db: AsyncSession, *, workspace_id: UUID, user_id: UUID, role: WorkspaceRole
    ) -> WorkspaceMember:
        member = WorkspaceMember(
            workspace_id=workspace_id, user_id=user_id, role=role
        )
        db.add(member)
        await db.flush()
        logger.info(
            "workspace_member.add",
            extra={
                "workspace_id": str(workspace_id),
                "user_id": str(user_id),
                "role": role.value if hasattr(role, "value") else str(role),
                "timestamp": datetime.now(timezone.utc).isoformat(),
            },
        )
        return member

    @staticmethod
    async def update_role(
        db: AsyncSession,
        *,
        workspace_id: UUID,
        user_id: UUID,
        role: WorkspaceRole,
    ) -> WorkspaceMember | None:
        member = await WorkspaceMemberDAO.get(
            db, workspace_id=workspace_id, user_id=user_id
        )
        if member:
            old_role = member.role
            member.role = role
            await db.flush()
            logger.info(
                "workspace_member.update_role",
                extra={
                    "workspace_id": str(workspace_id),
                    "user_id": str(user_id),
                    "old_role": old_role.value if hasattr(old_role, "value") else str(old_role),
                    "new_role": role.value if hasattr(role, "value") else str(role),
                    "timestamp": datetime.now(timezone.utc).isoformat(),
                },
            )
        return member

    @staticmethod
    async def remove(
        db: AsyncSession, *, workspace_id: UUID, user_id: UUID
    ) -> None:
        member = await WorkspaceMemberDAO.get(
            db, workspace_id=workspace_id, user_id=user_id
        )
        if member:
            role = member.role
            await db.delete(member)
            await db.flush()
            logger.info(
                "workspace_member.remove",
                extra={
                    "workspace_id": str(workspace_id),
                    "user_id": str(user_id),
                    "role": role.value if hasattr(role, "value") else str(role),
                    "timestamp": datetime.now(timezone.utc).isoformat(),
                },
            )

    @staticmethod
    async def list(
        db: AsyncSession, *, workspace_id: UUID
    ) -> List[WorkspaceMember]:
        stmt = select(WorkspaceMember).where(
            WorkspaceMember.workspace_id == workspace_id
        )
        result = await db.execute(stmt)
        return list(result.scalars().all())

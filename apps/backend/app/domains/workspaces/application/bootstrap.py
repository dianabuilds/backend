from __future__ import annotations

import logging

from sqlalchemy import select

from app.core.config import settings
from app.domains.users.infrastructure.models.user import User
from app.providers.db.session import db_session
from app.schemas.workspaces import WorkspaceRole, WorkspaceType

from ..infrastructure.models import Workspace, WorkspaceMember

logger = logging.getLogger(__name__)


async def ensure_global_workspace() -> None:
    """Ensure a single global system workspace exists.

    The workspace is created with type ``team`` and marked as system. All users
    whose role is in ``settings.security.admin_roles`` are granted access.
    """

    async with db_session() as session:
        result = await session.execute(
            select(Workspace).where(
                Workspace.kind == WorkspaceType.team,
                Workspace.is_system.is_(True),
            )
        )
        workspace = result.scalars().first()

        if workspace is None:
            owner_res = await session.execute(
                select(User)
                .where(User.role.in_(settings.security.admin_roles))
                .order_by(User.created_at)
                .limit(1)
            )
            owner = owner_res.scalars().first()
            if not owner:
                logger.warning("Cannot create global workspace: no admin user found")
                return

            workspace = Workspace(
                name="Global",
                slug="global",
                owner_user_id=owner.id,
                kind=WorkspaceType.team,
                is_system=True,
                settings_json={},
            )
            session.add(workspace)
            await session.flush()

        admin_res = await session.execute(
            select(User).where(User.role.in_(settings.security.admin_roles))
        )
        admins = admin_res.scalars().all()
        for user in admins:
            member_res = await session.execute(
                select(WorkspaceMember).where(
                    WorkspaceMember.workspace_id == workspace.id,
                    WorkspaceMember.user_id == user.id,
                )
            )
            member = member_res.scalars().first()
            desired_role = (
                WorkspaceRole.owner if user.id == workspace.owner_user_id else WorkspaceRole.editor
            )
            if member is None:
                session.add(
                    WorkspaceMember(
                        workspace_id=workspace.id,
                        user_id=user.id,
                        role=desired_role,
                    )
                )
            elif member.role == WorkspaceRole.viewer:
                member.role = desired_role

        await session.commit()
        logger.info("Ensured global workspace %s", workspace.id)


__all__ = ["ensure_global_workspace"]

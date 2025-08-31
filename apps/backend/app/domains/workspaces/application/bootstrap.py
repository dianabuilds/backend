from __future__ import annotations

import logging

from sqlalchemy import select

from app.core.config import settings
from app.core.db.session import db_session
from app.domains.users.infrastructure.models.user import User
from app.domains.workspaces.infrastructure.models import Workspace, WorkspaceMember
from app.schemas.workspaces import WorkspaceRole, WorkspaceType

logger = logging.getLogger(__name__)


async def ensure_global_workspace() -> None:
    """Ensure a single global system workspace exists.

    The workspace is created with type ``global`` and marked as system. All users
    whose role is in ``settings.security.admin_roles`` are granted access.
    """

    async with db_session() as session:
        result = await session.execute(
            select(Workspace).where(
                Workspace.type == WorkspaceType.global_,
                Workspace.is_system.is_(True),
            )
        )
        workspace = result.scalars().first()
        if workspace:
            return

        owner_res = await session.execute(
            select(User).where(User.role == "admin").order_by(User.created_at).limit(1)
        )
        owner = owner_res.scalars().first()
        if not owner:
            logger.warning("Cannot create global workspace: no admin user found")
            return

        workspace = Workspace(
            name="Global",
            slug="global",
            owner_user_id=owner.id,
            type=WorkspaceType.global_,
            is_system=True,
            settings_json={},
        )
        session.add(workspace)
        await session.flush()

        trusted_res = await session.execute(
            select(User).where(User.role.in_(settings.security.admin_roles))
        )
        for user in trusted_res.scalars().all():
            session.add(
                WorkspaceMember(
                    workspace_id=workspace.id,
                    user_id=user.id,
                    role=WorkspaceRole.owner,
                )
            )

        await session.commit()
        logger.info("Created global workspace %s", workspace.id)

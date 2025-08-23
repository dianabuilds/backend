from __future__ import annotations

from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

from .models import WorkspaceMember


class WorkspaceMemberDAO:
    @staticmethod
    async def get(db: AsyncSession, workspace_id: UUID, user_id: UUID) -> WorkspaceMember | None:
        stmt = (
            select(WorkspaceMember)
            .where(
                WorkspaceMember.workspace_id == workspace_id,
                WorkspaceMember.user_id == user_id,
            )
        )
        result = await db.execute(stmt)
        return result.scalars().first()

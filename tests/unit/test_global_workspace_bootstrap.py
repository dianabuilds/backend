import pytest
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker

from app.core.config import settings
from app.domains.users.infrastructure.models.user import User
from app.domains.workspaces.application.bootstrap import ensure_global_workspace
from app.domains.workspaces.infrastructure.models import Workspace, WorkspaceMember
from app.schemas.workspaces import WorkspaceRole


@pytest.mark.asyncio
async def test_ensure_global_workspace_respects_admin_roles(monkeypatch) -> None:
    engine = create_async_engine("sqlite+aiosqlite:///:memory:")
    async with engine.begin() as conn:
        await conn.run_sync(User.__table__.create)
        await conn.run_sync(Workspace.__table__.create)
        await conn.run_sync(WorkspaceMember.__table__.create)
    async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

    async def _db_session():
        async with async_session() as session:
            try:
                yield session
                await session.commit()
            finally:
                await session.close()

    monkeypatch.setattr("app.domains.workspaces.application.bootstrap.db_session", _db_session)
    monkeypatch.setattr(settings.security, "admin_roles", ["moderator"])

    async with async_session() as session:
        user = User(email="m@e", username="m", role="moderator", is_active=True)
        session.add(user)
        await session.commit()
        uid = user.id

    await ensure_global_workspace()

    async with async_session() as session:
        ws = (await session.execute(select(Workspace))).scalars().one()
        assert ws.owner_user_id == uid
        member = (
            (
                await session.execute(
                    select(WorkspaceMember).where(
                        WorkspaceMember.workspace_id == ws.id,
                        WorkspaceMember.user_id == uid,
                    )
                )
            )
            .scalars()
            .first()
        )
        assert member is not None
        assert member.role == WorkspaceRole.owner

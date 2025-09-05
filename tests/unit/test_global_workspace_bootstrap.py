import pytest
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker

from app.core.config import settings
from app.domains.users.infrastructure.models.user import User
from app.domains.workspaces.application.bootstrap import ensure_global_workspace
from app.domains.workspaces.infrastructure.models import Workspace, WorkspaceMember
from app.schemas.workspaces import WorkspaceRole, WorkspaceType


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


@pytest.mark.asyncio
async def test_existing_workspace_adds_moderator_access(monkeypatch) -> None:
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
        owner = User(email="o@e", username="o", role="moderator", is_active=True)
        mod = User(email="m@e", username="m", role="moderator", is_active=True)
        session.add_all([owner, mod])
        await session.flush()
        ws = Workspace(
            name="Global",
            slug="global",
            owner_user_id=owner.id,
            kind=WorkspaceType.team,
            is_system=True,
            settings_json={},
        )
        session.add(ws)
        await session.flush()
        session.add_all(
            [
                WorkspaceMember(workspace_id=ws.id, user_id=owner.id, role=WorkspaceRole.owner),
                WorkspaceMember(workspace_id=ws.id, user_id=mod.id, role=WorkspaceRole.viewer),
            ]
        )
        await session.commit()
        mod_id = mod.id
        ws_id = ws.id

    await ensure_global_workspace()

    async with async_session() as session:
        workspaces = (await session.execute(select(Workspace))).scalars().all()
        assert len(workspaces) == 1
        member = (
            (
                await session.execute(
                    select(WorkspaceMember).where(
                        WorkspaceMember.workspace_id == ws_id,
                        WorkspaceMember.user_id == mod_id,
                    )
                )
            )
            .scalars()
            .first()
        )
        assert member is not None
        assert member.role == WorkspaceRole.editor

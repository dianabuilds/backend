import uuid

import pytest
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker

from app.domains.users.application.user_profile_service import UserProfileService
from app.domains.users.infrastructure.models.user import User
from app.domains.users.infrastructure.repositories.user_repository import (
    UserRepository,
)


@pytest.mark.asyncio
async def test_update_default_workspace() -> None:
    engine = create_async_engine("sqlite+aiosqlite:///:memory:")
    async with engine.begin() as conn:
        await conn.run_sync(User.__table__.create)
    async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

    async with async_session() as session:
        user = User(id=uuid.uuid4())
        session.add(user)
        await session.commit()

        repo = UserRepository(session)
        service = UserProfileService(repo)

        wid = uuid.uuid4()
        updated = await service.update_default_workspace(user, wid)
        assert updated.default_workspace_id == wid

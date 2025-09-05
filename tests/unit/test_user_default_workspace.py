import os
import uuid

import pytest
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker

os.environ["TESTING"] = "1"
import app.providers.db.base  # noqa: F401
from app.domains.nodes.infrastructure.models.node import Node  # noqa: F401
from app.domains.users.application.user_profile_service import UserProfileService
from app.domains.users.infrastructure.models.user import User
from app.domains.users.infrastructure.repositories.user_repository import (
    UserRepository,
)
from app.schemas.user import UserOut


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
        user_out = UserOut.model_validate(updated)
        assert user_out.default_workspace_id == wid

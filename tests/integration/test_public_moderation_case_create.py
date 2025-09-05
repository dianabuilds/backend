import types
import uuid

import pytest
import pytest_asyncio
from fastapi import FastAPI
from httpx import ASGITransport, AsyncClient
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker

from app.api.deps import get_current_user, get_db
from app.domains.moderation.api.public_router import router as public_router
from app.domains.moderation.infrastructure.models.moderation_case_models import (
    CaseAttachment,
    ModerationCase,
)


@pytest_asyncio.fixture()
async def app_and_session():
    engine = create_async_engine("sqlite+aiosqlite:///:memory:")
    async with engine.begin() as conn:
        await conn.run_sync(ModerationCase.__table__.create)
        await conn.run_sync(CaseAttachment.__table__.create)
    async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

    app = FastAPI()
    app.include_router(public_router)

    async def override_db():
        async with async_session() as session:
            yield session

    app.dependency_overrides[get_db] = override_db
    return app, async_session


@pytest.mark.asyncio
async def test_requires_auth(app_and_session):
    app, _ = app_and_session
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        resp = await client.post(
            "/moderation/cases", json={"type": "support_request", "summary": "s"}
        )
        assert resp.status_code == 401


@pytest.mark.asyncio
async def test_create_case(app_and_session):
    app, async_session = app_and_session
    user = types.SimpleNamespace(id=uuid.uuid4())
    app.dependency_overrides[get_current_user] = lambda: user

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        payload = {
            "type": "support_request",
            "summary": "help",
            "reporter_contact": "a@b.c",
            "attachments": [{"url": "http://example.com/a.png"}],
        }
        resp = await client.post("/moderation/cases", json=payload)
        assert resp.status_code == 200
        case_id = uuid.UUID(resp.json()["id"])

    async with async_session() as session:
        case = await session.get(ModerationCase, case_id)
        assert case.reporter_id == user.id
        assert case.reporter_contact == "a@b.c"
        res = await session.execute(select(CaseAttachment).where(CaseAttachment.case_id == case.id))
        attachments = res.scalars().all()
        assert len(attachments) == 1
        assert attachments[0].url == "http://example.com/a.png"

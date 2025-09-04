from __future__ import annotations

import uuid

import pytest
import pytest_asyncio
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.domains.moderation.application.cases_service import CasesService
from app.domains.moderation.infrastructure.models.moderation_case_models import (
    CaseAttachment,
    CaseEvent,
    CaseLabel,
    CaseNote,
    ModerationCase,
    ModerationLabel,
)
from app.schemas.moderation_cases import (
    CaseAttachmentCreate,
    CaseCreate,
    CasePatch,
)


@pytest_asyncio.fixture()
async def session_factory():
    engine = create_async_engine(
        "sqlite+aiosqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    async with engine.begin() as conn:
        await conn.run_sync(ModerationCase.__table__.create)
        await conn.run_sync(CaseAttachment.__table__.create)
        await conn.run_sync(CaseNote.__table__.create)
        await conn.run_sync(CaseEvent.__table__.create)
        await conn.run_sync(ModerationLabel.__table__.create)
        await conn.run_sync(CaseLabel.__table__.create)
    async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    yield async_session
    await engine.dispose()


@pytest.mark.asyncio
async def test_create_and_get_case(session_factory: sessionmaker) -> None:
    service = CasesService()
    async with session_factory() as db:
        data = CaseCreate(
            type="support_request",
            summary="help",
            reporter_contact="a@b.c",
            attachments=[CaseAttachmentCreate(url="http://example.com/a.png")],
        )
        case_id = await service.create_case(db, data)
    async with session_factory() as db:
        res = await service.get_case(db, case_id)
        assert res is not None
        assert res.case.summary == "help"
        assert res.case.reporter_contact == "a@b.c"
        assert res.attachments[0].url == "http://example.com/a.png"


@pytest.mark.asyncio
async def test_patch_missing_case_returns_none(session_factory: sessionmaker) -> None:
    service = CasesService()
    async with session_factory() as db:
        res = await service.patch_case(db, uuid.uuid4(), CasePatch(summary="x"))
        assert res is None

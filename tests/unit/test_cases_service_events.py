from __future__ import annotations

import types
import uuid
from datetime import datetime, timedelta

import pytest
import pytest_asyncio
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker

from app.domains.moderation.application.cases_service import CasesService
from app.domains.moderation.infrastructure.models.moderation_case_models import (
    CaseEvent,
    CaseLabel,
    CaseNote,
    ModerationCase,
    ModerationLabel,
)
from app.providers.case_notifier import ICaseNotifier
from app.schemas.moderation_cases import CaseCreate, CaseNoteCreate, CasePatch


class DummyNotifier(ICaseNotifier):
    def __init__(self) -> None:
        self.called_with: uuid.UUID | None = None

    async def case_created(
        self, case_id: uuid.UUID
    ) -> None:  # pragma: no cover - simple store
        self.called_with = case_id


@pytest_asyncio.fixture()
async def session() -> AsyncSession:
    engine = create_async_engine("sqlite+aiosqlite:///:memory:")
    async with engine.begin() as conn:
        await conn.run_sync(ModerationCase.__table__.create)
        await conn.run_sync(CaseEvent.__table__.create)
        await conn.run_sync(CaseNote.__table__.create)
        await conn.run_sync(ModerationLabel.__table__.create)
        await conn.run_sync(CaseLabel.__table__.create)
    async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    async with async_session() as s:
        yield s


@pytest.mark.asyncio
async def test_create_case_sets_sla_and_notifies(
    session: AsyncSession, monkeypatch: pytest.MonkeyPatch
):
    service = CasesService()
    notifier = DummyNotifier()
    now = datetime.utcnow()
    monkeypatch.setattr(
        "app.domains.moderation.application.cases_service.datetime",
        types.SimpleNamespace(utcnow=lambda: now),
    )
    payload = CaseCreate(type="support_request", summary="s")
    case_id = await service.create_case(session, payload, notifier)
    assert notifier.called_with == case_id
    case = await session.get(ModerationCase, case_id)
    assert case.first_response_due_at == now + timedelta(minutes=30)
    assert case.due_at == now + timedelta(minutes=1440)


@pytest.mark.asyncio
async def test_patch_assign_and_add_note_create_events(session: AsyncSession):
    service = CasesService()
    case = ModerationCase(type="support_request", summary="s")
    session.add(case)
    await session.commit()
    await session.refresh(case)

    assignee = uuid.uuid4()
    await service.patch_case(session, case.id, CasePatch(assignee_id=assignee))
    note = await service.add_note(
        session, case.id, CaseNoteCreate(text="hi"), author_id=assignee
    )
    assert note is not None
    res = await session.execute(select(CaseEvent).where(CaseEvent.case_id == case.id))
    events = res.scalars().all()
    kinds = [e.kind for e in events]
    assert "assign" in kinds
    assert "add_note" in kinds

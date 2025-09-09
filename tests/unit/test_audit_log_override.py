from __future__ import annotations

import importlib
import sys
import uuid

import pytest
import pytest_asyncio
import sqlalchemy as sa
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker

app_module = importlib.import_module("apps.backend.app")
sys.modules.setdefault("app", app_module)

from app.domains.admin.infrastructure.models.audit_log import AuditLog  # noqa: E402
from app.domains.audit.application.audit_service import audit_log  # noqa: E402


@pytest_asyncio.fixture()
async def session() -> AsyncSession:
    engine = create_async_engine("sqlite+aiosqlite:///:memory:")
    async with engine.begin() as conn:
        await conn.run_sync(AuditLog.__table__.create)
    async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    async with async_session() as session:
        yield session


@pytest.mark.asyncio
async def test_audit_log_records_override(session: AsyncSession) -> None:
    await audit_log(session, actor_id=str(uuid.uuid4()), action="node_update", resource_type="node", resource_id="123",
                    before={"a": 1}, after={"a": 2}, reason="test", override=True)
    logs = (await session.execute(sa.select(AuditLog))).scalars().all()
    assert len(logs) == 1
    log = logs[0]
    assert log.override is True
    assert log.reason == "test"

import logging
from uuid import uuid4

import pytest
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.domains.admin.infrastructure.models.audit_log import AuditLog
from app.domains.audit.application.audit_service import audit_log
from app.domains.nodes.models import NodeItem  # noqa: F401


@pytest.mark.asyncio
async def test_audit_log_stores_workspace_and_logs_event(
    db_session: AsyncSession, caplog
):
    await db_session.run_sync(
        lambda s: AuditLog.__table__.drop(s.bind, checkfirst=True)
    )
    await db_session.run_sync(
        lambda s: AuditLog.__table__.create(s.bind, checkfirst=True)
    )
    ws_id = uuid4()
    actor_id = uuid4()
    with caplog.at_level(logging.INFO, logger="app.api.rum_metrics"):
        await audit_log(
            db_session,
            actor_id=str(actor_id),
            action="quest_publish",
            resource_type="quest",
            resource_id="q1",
            workspace_id=str(ws_id),
            node_type="quest",
        )
    await db_session.commit()
    res = await db_session.execute(
        select(AuditLog).where(AuditLog.workspace_id == ws_id)
    )
    log_entry = res.scalar_one()
    assert log_entry.workspace_id == ws_id
    assert any(
        "publish" in r.getMessage() and str(ws_id) in r.getMessage()
        for r in caplog.records
    )
    await db_session.run_sync(
        lambda s: AuditLog.__table__.drop(s.bind, checkfirst=True)
    )

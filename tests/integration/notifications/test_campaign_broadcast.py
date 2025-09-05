from __future__ import annotations

from uuid import UUID, uuid4

import pytest
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from tests.integration.conftest import test_engine
from tests.integration.db_utils import TestUser, create_user
from workers.notifications import campaign_queue

from app.domains.notifications.application.broadcast_service import (
    run_campaign,
    start_campaign_async,
)
from app.domains.notifications.infrastructure.models.campaign_models import (
    CampaignStatus,
    NotificationCampaign,
)
from app.domains.notifications.infrastructure.models.notification_models import (
    Notification,
)


@pytest.mark.asyncio
async def test_run_campaign(db_session: AsyncSession, test_user: TestUser) -> None:
    async with test_engine.begin() as conn:
        await conn.run_sync(NotificationCampaign.__table__.create)
        await conn.run_sync(Notification.__table__.create)

    user2 = TestUser(email="u2@example.com", username="user2", password_hash="x", is_active=False)
    await create_user(user2, db_session)

    camp = NotificationCampaign(
        title="Hello",
        message="Msg",
        type="system",
        filters={"is_active": True},
        status=CampaignStatus.queued,
        created_by=UUID(test_user.id),
    )
    db_session.add(camp)
    await db_session.commit()
    await db_session.refresh(camp)

    await run_campaign(db_session, camp.id)

    camp_db = await db_session.get(NotificationCampaign, camp.id)
    assert camp_db
    assert camp_db.status == CampaignStatus.done
    assert camp_db.total == 1
    assert camp_db.sent == 1
    assert camp_db.failed == 0

    res = await db_session.execute(select(Notification))
    notifs = res.scalars().all()
    assert len(notifs) == 1
    assert notifs[0].user_id == UUID(test_user.id)


def test_start_campaign_async_enqueues_job() -> None:
    if campaign_queue is None:
        pytest.skip("queue not configured")
    cid = uuid4()
    start_campaign_async(cid)
    assert campaign_queue.count == 1

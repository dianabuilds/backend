import pytest
from uuid import uuid4
from contextlib import asynccontextmanager
from sqlalchemy import select

from app.domains.notifications.infrastructure.models.campaign_models import (
    NotificationCampaign,
    CampaignStatus,
)
from app.domains.content import service as content_service
from app.domains.notifications import service as notif_service


@pytest.mark.asyncio
async def test_content_published_creates_campaign(db_session):
    @asynccontextmanager
    async def _cm():
        yield db_session

    # Patch db_session in notification service to use test session
    monkey = pytest.MonkeyPatch()
    monkey.setattr(notif_service, "db_session", _cm)

    # Ensure table exists in test database
    await db_session.run_sync(
        lambda sync_sess: NotificationCampaign.__table__.create(
            sync_sess.get_bind(), checkfirst=True
        )
    )

    await content_service.publish_content(uuid4(), "slug-1", uuid4())

    res = await db_session.execute(select(NotificationCampaign))
    camp = res.scalars().first()
    assert camp is not None
    assert camp.status == CampaignStatus.draft
    monkey.undo()

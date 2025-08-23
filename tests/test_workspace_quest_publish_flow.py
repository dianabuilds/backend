import pytest
from contextlib import asynccontextmanager
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.domains.workspaces.infrastructure.models import Workspace
from app.domains.quests.infrastructure.models.quest_models import Quest
from app.domains.notifications.infrastructure.models.campaign_models import (
    NotificationCampaign,
    CampaignStatus,
)
from app.domains.quests.authoring import create_quest
from app.schemas.quest import QuestCreate
from app.schemas.content_common import ContentStatus
from app.domains.content.service import validate_transition, publish_content
from app.core.db import session as core_session


@pytest.mark.asyncio
async def test_workspace_quest_publish_flow(db_session: AsyncSession, test_user) -> None:
    # create required tables
    await db_session.run_sync(
        lambda s: Workspace.__table__.create(s.get_bind(), checkfirst=True)
    )
    await db_session.run_sync(
        lambda s: Quest.__table__.create(s.get_bind(), checkfirst=True)
    )
    await db_session.run_sync(
        lambda s: NotificationCampaign.__table__.create(s.get_bind(), checkfirst=True)
    )

    ws = Workspace(name="ws", slug="ws", owner_user_id=test_user.id)
    db_session.add(ws)
    await db_session.commit()
    await db_session.refresh(ws)

    payload = QuestCreate(title="Q1", nodes=[], custom_transitions={})
    quest = await create_quest(db_session, payload=payload, author=test_user, workspace_id=ws.id)
    assert quest.workspace_id == ws.id
    assert quest.status == ContentStatus.draft

    # attempt to publish without review should fail
    with pytest.raises(ValueError):
        validate_transition(quest.status, ContentStatus.published)

    # move quest to review
    validate_transition(quest.status, ContentStatus.in_review)
    quest.status = ContentStatus.in_review
    await db_session.commit()

    @asynccontextmanager
    async def _cm():
        yield db_session

    monkey = pytest.MonkeyPatch()
    monkey.setattr(core_session, "db_session", _cm)

    # publish quest
    validate_transition(quest.status, ContentStatus.published)
    quest.status = ContentStatus.published
    await db_session.commit()
    await publish_content(quest.id, quest.slug, quest.author_id)

    res = await db_session.execute(select(NotificationCampaign))
    camp = res.scalars().first()
    assert camp is not None
    assert camp.status == CampaignStatus.draft

    monkey.undo()

    # cleanup
    await db_session.run_sync(
        lambda s: NotificationCampaign.__table__.drop(s.get_bind(), checkfirst=True)
    )
    await db_session.run_sync(
        lambda s: Quest.__table__.drop(s.get_bind(), checkfirst=True)
    )
    await db_session.run_sync(
        lambda s: Workspace.__table__.drop(s.get_bind(), checkfirst=True)
    )

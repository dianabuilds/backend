import pytest

from domains.platform.moderation.application.service import (
    PlatformModerationService,
)
from domains.platform.moderation.domain.dtos import (
    SanctionStatus,
    SanctionType,
)


@pytest.mark.asyncio
async def test_issue_sanction_promotes_user_status():
    service = PlatformModerationService()
    await service.ensure_user_stub(user_id="user-1", username="alice")

    dto = await service.issue_sanction(
        "user-1",
        {
            "type": SanctionType.ban.value,
            "reason": "abuse",
        },
        actor_id="moderator:test",
    )

    assert dto.status == SanctionStatus.active
    assert service._users["user-1"].status == "banned"


@pytest.mark.asyncio
async def test_get_overview_returns_summary():
    service = PlatformModerationService()
    overview = await service.get_overview(limit=5)

    assert overview.complaints_new["count"] >= 0
    assert overview.tickets["open"] >= 0
    assert isinstance(overview.last_sanctions, list)

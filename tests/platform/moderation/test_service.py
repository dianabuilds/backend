import pytest
from apps.backend.domains.platform.moderation.domain.dtos import (
    ContentType,
    SanctionStatus,
    SanctionType,
)
from apps.backend.domains.platform.moderation.application.service import (
    PlatformModerationService,
)


@pytest.mark.asyncio
async def test_issue_and_cancel_sanction():
    svc = PlatformModerationService()
    sanction = await svc.issue_sanction(
        "u-102",
        {"type": "mute", "reason": "test", "duration_hours": 2},
    )
    assert sanction.type == SanctionType.mute
    assert sanction.status in {SanctionStatus.active, SanctionStatus.expired}

    updated = await svc.update_sanction("u-102", sanction.id, {"status": "canceled"})
    assert updated.status == SanctionStatus.canceled


@pytest.mark.asyncio
async def test_list_content_filters_reports():
    svc = PlatformModerationService()
    result = await svc.list_content(
        type=ContentType.node, has_reports=True, limit=10, cursor=None
    )
    assert result["items"], "expected seeded content with reports"
    assert all(item.type == ContentType.node for item in result["items"])


@pytest.mark.asyncio
async def test_overview_contains_sanctions_and_cards():
    svc = PlatformModerationService()
    overview = await svc.get_overview(limit=5)
    assert overview.last_sanctions
    assert overview.cards
    assert "complaint_sources" in overview.charts


@pytest.mark.asyncio
async def test_ai_rule_history_enriched():
    svc = PlatformModerationService()
    listing = await svc.list_rules(limit=10, cursor=None)
    assert listing["items"]
    rule_id = listing["items"][0].id
    await svc.update_rule(rule_id, {"enabled": False})
    hist = await svc.rules_history(limit=10, cursor=None)
    assert any(entry["rule_id"] == rule_id for entry in hist["items"])

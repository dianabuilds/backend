from __future__ import annotations

import pytest

from ..application import overview


@pytest.mark.asyncio
async def test_get_overview_aggregates_metrics(moderation_service, moderation_data):
    service = moderation_service

    result = await overview.get_overview(service, limit=5)

    assert result.complaints_new["count"] == 1
    assert result.content_queues["node"] == 2
    assert result.tickets["open"] >= 1
    assert abs(result.charts["avg_response_time_hours"] - 12.0) < 1e-6
    assert abs(result.charts["ai_autodecisions_share"] - 0.5) < 1e-6
    card_ids = {card.id for card in result.cards}
    assert moderation_data["users"]["bob"] in card_ids
    assert (
        result.last_sanctions
        and result.last_sanctions[0].id == moderation_data["sanctions"]["ban"]
    )


@pytest.mark.asyncio
async def test_get_overview_limits_last_sanctions(moderation_service):
    service = moderation_service

    result = await overview.get_overview(service, limit=1)

    assert len(result.last_sanctions) == 1

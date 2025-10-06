from __future__ import annotations

import pytest

from ....application import ai_rules


@pytest.mark.asyncio
async def test_create_rule_adds_entry(moderation_service):
    service = moderation_service
    dto = await ai_rules.create_rule(
        service,
        body={
            "category": "abuse",
            "thresholds": {"abuse": 0.7},
            "actions": {"auto_flag": True},
            "enabled": False,
        },
        actor_id="mod-lena",
    )

    assert dto.category == "abuse"
    assert dto.history
    assert dto.id in service._ai_rules


@pytest.mark.asyncio
async def test_update_rule_tracks_changes(moderation_service, moderation_data):
    service = moderation_service
    rule_id = moderation_data["ai_rules"]["spam"]

    dto = await ai_rules.update_rule(
        service,
        rule_id=rule_id,
        body={"thresholds": {"spam": 0.9}, "enabled": False},
        actor_id="mod-lena",
    )

    assert dto.thresholds["spam"] == 0.9
    rule = service._ai_rules[rule_id]
    assert rule.history and rule.history[-1]["changes"]["thresholds"] == {"spam": 0.9}


@pytest.mark.asyncio
async def test_test_rule_flags_high_scores(moderation_service, moderation_data):
    service = moderation_service
    rule_id = moderation_data["ai_rules"]["spam"]

    result = await ai_rules.test_rule(
        service,
        payload={"rule_id": rule_id, "scores": {"spam": 0.95, "abuse": 0.1}},
    )

    assert result["decision"] == "flag"
    assert "spam" in result["labels"]


@pytest.mark.asyncio
async def test_get_rule_missing_raises(moderation_service):
    service = moderation_service
    with pytest.raises(KeyError):
        await ai_rules.get_rule(service, "missing")

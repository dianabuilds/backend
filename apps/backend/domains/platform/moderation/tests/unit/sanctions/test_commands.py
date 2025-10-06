from __future__ import annotations

import pytest

from ....application import sanctions
from ....domain.dtos import SanctionStatus, SanctionType


@pytest.mark.asyncio
async def test_issue_sanction_creates_record(moderation_service, moderation_data):
    service = moderation_service
    user_id = moderation_data["users"]["alice"]

    dto = await sanctions.issue_sanction(
        service,
        user_id=user_id,
        body={"type": "mute", "duration_hours": 4, "reason": "temporary mute"},
        actor_id="mod-lena",
    )

    assert dto.type == SanctionType.mute
    assert dto.status == SanctionStatus.active
    assert dto.id in service._sanctions


@pytest.mark.asyncio
async def test_issue_sanction_validates_type(moderation_service, moderation_data):
    service = moderation_service
    user_id = moderation_data["users"]["alice"]
    with pytest.raises(ValueError):
        await sanctions.issue_sanction(
            service, user_id=user_id, body={"type": "invalid"}
        )


@pytest.mark.asyncio
async def test_update_sanction_revokes_active_ban(moderation_service, moderation_data):
    service = moderation_service
    sanction_id = moderation_data["sanctions"]["ban"]
    user_id = moderation_data["users"]["bob"]

    dto = await sanctions.update_sanction(
        service,
        user_id=user_id,
        sanction_id=sanction_id,
        body={"revoke": True, "reason": "appeal approved"},
        actor_id="mod-lena",
    )

    assert dto.status == SanctionStatus.canceled
    sanction = service._sanctions[sanction_id]
    assert sanction.revoked_by == "mod-lena"


@pytest.mark.asyncio
async def test_add_note_persists_entry(moderation_service, moderation_data):
    service = moderation_service
    user_id = moderation_data["users"]["bob"]

    note = await sanctions.add_note(
        service,
        user_id=user_id,
        body={"text": "monitoring", "pinned": True},
        actor_id="mod-lena",
        actor_name="Lena",
    )

    assert note.text == "monitoring"
    assert note.pinned is True
    assert note.id in service._notes


@pytest.mark.asyncio
async def test_add_note_missing_user_raises(moderation_service):
    service = moderation_service
    with pytest.raises(KeyError):
        await sanctions.add_note(service, user_id="missing", body={"text": "hi"})

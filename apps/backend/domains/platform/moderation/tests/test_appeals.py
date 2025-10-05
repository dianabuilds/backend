from __future__ import annotations

from datetime import UTC, datetime

import pytest

from ..application import appeals
from ..domain.dtos import SanctionStatus


@pytest.mark.asyncio
async def test_decide_appeal_cancels_sanction(moderation_service, moderation_data):
    service = moderation_service
    appeal_id = moderation_data["appeals"]["pending"]
    sanction_id = moderation_data["sanctions"]["ban"]

    result = await appeals.decide_appeal(
        service,
        appeal_id=appeal_id,
        body={"result": "approved", "reason": "evidence updated"},
        actor_id="mod-lena",
    )

    assert result["status"] == "approved"
    sanction = service._sanctions[sanction_id]
    assert sanction.status == SanctionStatus.canceled
    assert sanction.revoked_by == "mod-lena"


@pytest.mark.asyncio
async def test_get_appeal_missing_raises(moderation_service):
    service = moderation_service
    with pytest.raises(KeyError):
        await appeals.get_appeal(service, "missing")


class DummyAppealsRepository:
    def __init__(self) -> None:
        self.fetch_calls: list[list[str]] = []
        self.record_kwargs: dict[str, str] | None = None

    async def fetch_many(self, appeal_ids):
        ids = [str(aid) for aid in appeal_ids]
        self.fetch_calls.append(ids)
        decided_at = datetime(2025, 1, 6, tzinfo=UTC)
        return {
            aid: {
                "status": "approved",
                "decided_at": decided_at,
                "decided_by": "repo-mod",
                "decision_reason": "db",
                "meta": {"history": ["repo"]},
            }
            for aid in ids
        }

    async def fetch_appeal(self, appeal_id):
        return {
            "status": "approved",
            "decided_at": datetime(2025, 1, 6, tzinfo=UTC),
            "decided_by": "repo-mod",
            "decision_reason": "db",
            "meta": {"history": ["repo"]},
        }

    async def record_decision(
        self, appeal_id, *, status, decided_at, decided_by, decision_reason, meta
    ):
        self.record_kwargs = {
            "appeal_id": appeal_id,
            "status": status,
            "decided_by": decided_by,
        }
        return {
            "status": status,
            "decided_at": decided_at,
            "decided_by": decided_by,
            "decision_reason": decision_reason,
            "meta": meta,
        }


@pytest.mark.asyncio
async def test_list_appeals_merges_repository(moderation_service):
    service = moderation_service
    repo = DummyAppealsRepository()

    result = await appeals.list_appeals(service, repository=repo)

    assert repo.fetch_calls
    assert all(item.status == "approved" for item in result["items"])
    assert all(item.decided_by == "repo-mod" for item in result["items"])
    assert all(item.meta.get("history") == ["repo"] for item in result["items"])


@pytest.mark.asyncio
async def test_decide_appeal_uses_repository(moderation_service, moderation_data):
    service = moderation_service
    repo = DummyAppealsRepository()
    appeal_id = moderation_data["appeals"]["pending"]

    result = await appeals.decide_appeal(
        service,
        appeal_id,
        body={"result": "approved", "reason": "ok"},
        actor_id="mod-lena",
        repository=repo,
    )

    assert repo.record_kwargs == {
        "appeal_id": appeal_id,
        "status": "approved",
        "decided_by": "mod-lena",
    }
    assert result["db_state"]["decided_by"] == "mod-lena"

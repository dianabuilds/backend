from __future__ import annotations

import asyncio
from datetime import UTC, datetime
from typing import Any

import pytest

from domains.platform.moderation.application.appeals import commands as appeal_commands
from domains.platform.moderation.application.appeals import queries as appeal_queries
from domains.platform.moderation.application.common import isoformat_utc
from domains.platform.moderation.domain.dtos import AppealDTO
from domains.platform.moderation.domain.records import AppealRecord


class StubRepo:
    def __init__(self) -> None:
        self.decisions: list[dict[str, Any]] = []

    async def fetch_many(self, appeal_ids):
        ids = list(appeal_ids)
        return {
            aid: {
                "status": "approved",
                "decided_at": datetime(2025, 1, 2, tzinfo=UTC),
                "decided_by": "moderator",
                "decision_reason": "ok",
                "meta": {"source": "repo"},
            }
            for aid in ids
        }

    async def fetch_appeal(self, appeal_id: str):
        if appeal_id != "a1":
            return None
        return {
            "status": "pending",
            "decided_at": datetime(2025, 1, 3, tzinfo=UTC),
            "decided_by": "system",
            "decision_reason": "",
            "meta": {"source": "repo"},
        }

    async def record_decision(
        self,
        appeal_id: str,
        *,
        status: str,
        decided_at: datetime | None,
        decided_by: str | None,
        decision_reason: str | None,
        meta: dict[str, Any],
    ) -> dict[str, Any]:
        payload = {
            "appeal_id": appeal_id,
            "status": status,
            "decided_at": decided_at,
            "decided_by": decided_by,
            "decision_reason": decision_reason,
            "meta": meta,
        }
        self.decisions.append(payload)
        return {
            "status": status,
            "decided_at": decided_at,
            "decided_by": decided_by,
            "decision_reason": decision_reason,
            "meta": meta,
        }


class StubService:
    def __init__(self) -> None:
        self._appeals = {
            "a1": AppealRecord(
                id="a1",
                target_type="content",
                target_id="c1",
                user_id="u1",
                text="Please review",
                status="open",
                created_at=datetime(2025, 1, 1, tzinfo=UTC),
                decided_at=None,
                decided_by=None,
                decision_reason=None,
                meta={},
            )
        }
        self._reports: dict[str, dict[str, Any]] = {}
        self._sanctions: dict[str, Any] = {}
        from asyncio import Lock

        self._lock = Lock()

    def _now(self) -> datetime:
        return datetime(2025, 1, 2, tzinfo=UTC)

    def _report_to_dto(self, report: dict[str, Any]) -> dict[str, Any]:
        return report

    def _appeal_to_dto(self, appeal: AppealRecord) -> AppealDTO:
        return AppealDTO(
            id=appeal.id,
            target_type=appeal.target_type,
            target_id=appeal.target_id,
            user_id=appeal.user_id,
            text=appeal.text,
            status=appeal.status,
            created_at=isoformat_utc(appeal.created_at),
            decided_at=isoformat_utc(appeal.decided_at),
            decided_by=appeal.decided_by,
            decision_reason=appeal.decision_reason,
            meta=dict(appeal.meta),
        )


def _run(awaitable):
    return asyncio.run(awaitable)  # type: ignore[arg-type]


def test_list_appeals_returns_payload() -> None:
    repo = StubRepo()
    result = _run(
        appeal_queries.list_appeals(
            StubService(),
            limit=10,
            repository=repo,
        )
    )
    assert isinstance(result["items"], list)
    assert result["items"][0]["id"] == "a1"
    assert result["items"][0]["meta"].get("source") == "repo"


def test_get_appeal_returns_dto() -> None:
    repo = StubRepo()
    result = _run(
        appeal_queries.get_appeal(
            StubService(),
            "a1",
            repository=repo,
        )
    )
    assert isinstance(result, dict)
    assert result["id"] == "a1"
    assert result["meta"].get("source") == "repo"


def test_get_appeal_not_found() -> None:
    repo = StubRepo()
    with pytest.raises(KeyError):
        _run(appeal_queries.get_appeal(StubService(), "missing", repository=repo))


def test_decide_appeal_returns_payload() -> None:
    repo = StubRepo()
    result = _run(
        appeal_commands.decide_appeal(
            StubService(),
            "a1",
            {"result": "approved"},
            actor_id="mod",
            repository=repo,
        )
    )
    assert result["status"] == "approved"
    assert repo.decisions and repo.decisions[0]["appeal_id"] == "a1"


def test_decide_appeal_missing() -> None:
    repo = StubRepo()
    with pytest.raises(KeyError):
        _run(
            appeal_commands.decide_appeal(
                StubService(),
                "missing",
                {"result": "approved"},
                actor_id="mod",
                repository=repo,
            )
        )

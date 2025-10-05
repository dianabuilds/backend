from __future__ import annotations

import asyncio
from datetime import UTC, datetime
from typing import Any

from domains.platform.moderation.application.appeals.exceptions import (
    ModerationAppealError,
)
from domains.platform.moderation.application.appeals.repository import AppealsRepository
from domains.platform.moderation.application.appeals.use_cases import (
    UseCaseResult,
    decide_appeal,
    get_appeal,
    list_appeals,
)
from domains.platform.moderation.domain.dtos import AppealDTO
from domains.platform.moderation.domain.records import AppealRecord
from domains.platform.moderation.application.common import isoformat_utc


class StubRepo(AppealsRepository):
    def __init__(self) -> None:  # type: ignore[no-untyped-def]
        self._engine = None

    async def list_appeals(self, **kwargs: Any) -> dict[str, Any]:
        return {"items": [{"id": "a1"}], "next_cursor": None}

    async def get_appeal(self, appeal_id: str) -> AppealRecord:
        if appeal_id != "a1":
            raise KeyError(appeal_id)
        return AppealRecord(
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

    async def decide_appeal(
        self, appeal_id: str, *, body: dict[str, Any], actor_id: str | None
    ) -> dict[str, Any]:
        if appeal_id != "a1":
            raise KeyError(appeal_id)
        return {
            "appeal_id": appeal_id,
            "status": body.get("status", "approved"),
            "actor": actor_id,
        }

    async def fetch_many(self, appeal_ids):  # type: ignore[override]
        return {}

    async def fetch_appeal(self, appeal_id: str):  # type: ignore[override]
        return None


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
    result = _run(list_appeals(StubService(), repo, limit=10))
    assert isinstance(result, UseCaseResult)
    assert result.payload["items"][0]["id"] == "a1"


def test_get_appeal_returns_dto() -> None:
    repo = StubRepo()
    result = _run(get_appeal(StubService(), repo, "a1"))
    assert result.payload["id"] == "a1"


def test_get_appeal_not_found() -> None:
    repo = StubRepo()
    try:
        _run(get_appeal(StubService(), repo, "missing"))
    except ModerationAppealError as exc:
        assert exc.code == "appeal_not_found"
    else:
        raise AssertionError("expected ModerationAppealError")


def test_decide_appeal_returns_payload() -> None:
    repo = StubRepo()
    result = _run(
        decide_appeal(
            StubService(),
            repo,
            appeal_id="a1",
            payload={"status": "approved"},
            actor_id="mod",
        )
    )
    assert result.payload["status"] == "approved"

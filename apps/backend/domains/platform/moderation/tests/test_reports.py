from __future__ import annotations

from datetime import UTC, datetime

import pytest

from ..application import reports
from ..domain.dtos import ReportStatus


@pytest.mark.asyncio
async def test_list_reports_filters_by_status(moderation_service):
    service = moderation_service

    new_reports = await reports.list_reports(service, status=ReportStatus.new)
    assert all(item.status == ReportStatus.new for item in new_reports["items"])

    resolved_reports = await reports.list_reports(service, status="resolved")
    assert all(
        item.status == ReportStatus.resolved for item in resolved_reports["items"]
    )


@pytest.mark.asyncio
async def test_resolve_report_updates_state(moderation_service, moderation_data):
    service = moderation_service
    report_id = moderation_data["reports"]["open"]
    service._reports[report_id].object_id = moderation_data["sanctions"]["ban"]

    result = await reports.resolve_report(
        service,
        report_id=report_id,
        body={"result": "valid", "decision": "ban", "notes": "Confirmed"},
        actor_id="mod-lena",
    )

    assert result["status"] == ReportStatus.valid.value
    report = service._reports[report_id]
    assert report.status == ReportStatus.valid
    assert report.resolved_at is not None
    assert report.updates and report.updates[0]["actor"] == "mod-lena"
    sanction_meta = service._sanctions[moderation_data["sanctions"]["ban"]].meta
    assert report_id in sanction_meta.get("related_reports", [])


@pytest.mark.asyncio
async def test_get_report_missing_raises(moderation_service):
    service = moderation_service
    with pytest.raises(KeyError):
        await reports.get_report(service, "nope")


class DummyReportsRepository:
    def __init__(self) -> None:
        self.fetch_calls: list[list[str]] = []
        self.record_kwargs: dict[str, str] | None = None

    async def fetch_many(self, report_ids):
        ids = [str(rid) for rid in report_ids]
        self.fetch_calls.append(ids)
        resolved_at = datetime(2025, 1, 3, tzinfo=UTC)
        return {
            rid: {
                "status": "valid",
                "decision": "ban",
                "notes": "repo",
                "resolved_at": resolved_at,
                "updates": [{"actor": "repo"}],
                "meta": {"source": "repo"},
            }
            for rid in ids
        }

    async def record_resolution(
        self, report_id, *, status, decision, notes, actor_id, resolved_at, payload
    ):
        self.record_kwargs = {
            "report_id": report_id,
            "status": status,
            "decision": decision,
            "notes": notes,
            "actor_id": actor_id,
        }
        return {
            "status": status,
            "decision": decision,
            "notes": notes,
            "resolved_at": (
                resolved_at.isoformat().replace("+00:00", "Z") if resolved_at else None
            ),
            "history_entry": {"actor": actor_id},
        }


@pytest.mark.asyncio
async def test_list_reports_merges_repository_data(moderation_service):
    service = moderation_service
    repo = DummyReportsRepository()

    result = await reports.list_reports(service, limit=3, repository=repo)

    assert repo.fetch_calls, "repository was not queried"
    assert all(item.meta.get("source") == "repo" for item in result["items"])
    assert all(item.status == ReportStatus.valid for item in result["items"])


@pytest.mark.asyncio
async def test_resolve_report_uses_repository(moderation_service, moderation_data):
    service = moderation_service
    repo = DummyReportsRepository()
    report_id = moderation_data["reports"]["open"]
    service._reports[report_id].object_id = moderation_data["sanctions"]["ban"]

    result = await reports.resolve_report(
        service,
        report_id,
        body={"result": "valid", "decision": "ban", "notes": "repo"},
        actor_id="mod-lena",
        repository=repo,
    )

    assert repo.record_kwargs == {
        "report_id": report_id,
        "status": "valid",
        "decision": "ban",
        "notes": "repo",
        "actor_id": "mod-lena",
    }
    assert result["db_state"]["history_entry"]["actor"] == "mod-lena"

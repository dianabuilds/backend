import datetime as dt

import pytest

from domains.platform.moderation.application.presenters import (
    build_list_response,
    merge_history_prepend,
    merge_metadata,
)
from domains.platform.moderation.application.content.presenter import (
    build_decision_response as build_content_decision,
    merge_summary_with_db,
)
from domains.platform.moderation.application.reports.presenter import (
    build_reports_list_response,
    build_resolution_response,
    merge_report_with_db,
)
from domains.platform.moderation.application.tickets.presenter import (
    build_messages_response,
    build_tickets_list_response,
    merge_ticket_with_db,
    message_from_db,
)
from domains.platform.moderation.application.appeals.presenter import (
    build_appeals_list_response,
    build_decision_response as build_appeal_decision,
    merge_appeal_with_db,
)
from domains.platform.moderation.application.ai_rules.presenter import (
    build_history_response,
    build_rules_list_response,
    build_test_response,
)
from domains.platform.moderation.domain.dtos import (
    AIRuleDTO,
    AppealDTO,
    ContentStatus,
    ContentSummary,
    ContentType,
    ReportDTO,
    ReportStatus,
    TicketDTO,
    TicketMessageDTO,
    TicketPriority,
    TicketStatus,
)


@pytest.fixture()
def sample_summary() -> ContentSummary:
    return ContentSummary(
        id="node-1",
        type=ContentType.node,
        author_id="author-original",
        created_at="2025-01-01T00:00:00Z",
        preview="orig",
        status=ContentStatus.pending,
        meta={"node_status": "draft"},
    )


def test_merge_metadata_skips_none() -> None:
    assert merge_metadata({"a": 1}, {"a": None, "b": 2}) == {"a": 1, "b": 2}


def test_merge_history_prepend_list() -> None:
    assert merge_history_prepend([{"id": 1}], [{"id": 2}]) == [{"id": 2}, {"id": 1}]


def test_merge_summary_with_db_overrides_and_merges(
    sample_summary: ContentSummary,
) -> None:
    db_info = {
        "author_id": "author-db",
        "created_at": "2025-01-02T12:00:00Z",
        "title": "from-db",
        "moderation_status": "hidden",
        "moderation_history": [{"action": "hide"}],
        "node_status": "published",
        "moderation_status_updated_at": "2025-01-02T12:00:00Z",
    }
    merged = merge_summary_with_db(sample_summary, db_info)
    assert merged.author_id == "author-db"
    assert merged.preview == "from-db"
    assert merged.status == ContentStatus.hidden
    assert merged.meta["node_status"] == "published"
    assert merged.meta["moderation_status"] == "hidden"
    assert merged.moderation_history == [{"action": "hide"}]


def test_build_content_decision_response_merges_history() -> None:
    decision = {"action": "hide"}
    db_record = {
        "status": "hidden",
        "history_entry": {"status": "hidden", "decided_at": "2025-01-02T12:00:00Z"},
    }
    resp = build_content_decision(
        "node-1", status="hidden", decision=decision, db_record=db_record
    )
    assert resp["moderation_status"] == "hidden"
    assert resp["decision"]["decided_at"] == "2025-01-02T12:00:00Z"


@pytest.fixture()
def sample_report() -> ReportDTO:
    return ReportDTO(
        id="rep-1",
        object_type="node",
        object_id="node-1",
        reporter_id="u-1",
        category="abuse",
    )


def test_merge_report_with_db_prepend_history(sample_report: ReportDTO) -> None:
    db_info = {
        "status": "valid",
        "decision": "ban",
        "notes": "updated",
        "resolved_at": dt.datetime(2025, 1, 2, tzinfo=dt.UTC),
        "updates": [{"actor": "moderator"}],
        "meta": {"source": "db"},
    }
    merged = merge_report_with_db(sample_report, db_info)
    assert merged.status == ReportStatus.valid

    assert merged.decision == "ban"

    assert merged.resolved_at is not None

    assert merged.resolved_at.endswith("Z")

    assert merged.updates and merged.updates[0]["actor"] == "moderator"
    assert merged.meta["source"] == "db"


def test_build_resolution_response_includes_db_state() -> None:
    resp = build_resolution_response(
        "rep-1",
        status="valid",
        decision="ban",
        notes="note",
        resolved_at="2025-01-02T12:00:00Z",
        db_record={"history_entry": {"actor": "mod"}},
    )
    assert resp["db_state"]["history_entry"]["actor"] == "mod"


@pytest.fixture()
def sample_ticket() -> TicketDTO:
    return TicketDTO(
        id="tic-1",
        title="Ticket",
        author_id="user",
    )


def test_merge_ticket_with_db_coerces_and_merges(sample_ticket: TicketDTO) -> None:
    db_info = {
        "status": "progress",
        "priority": "high",
        "assignee_id": "agent",
        "updated_at": dt.datetime(2025, 1, 3, tzinfo=dt.UTC),
        "last_message_at": dt.datetime(2025, 1, 3, 12, tzinfo=dt.UTC),
        "unread_count": 3,
        "meta": {"channel": "email"},
    }
    merged = merge_ticket_with_db(sample_ticket, db_info)
    assert merged.status == TicketStatus.progress
    assert merged.priority == TicketPriority.high
    assert merged.assignee_id == "agent"
    assert merged.unread_count == 3
    assert merged.meta["channel"] == "email"


def test_message_from_db_constructs_dto() -> None:
    dto = message_from_db(
        {
            "id": "msg-1",
            "ticket_id": "tic-1",
            "author_id": "user",
            "text": "hi",
            "internal": True,
            "author_name": "Agent",
            "created_at": dt.datetime(2025, 1, 3, tzinfo=dt.UTC),
            "attachments": [],
        }
    )
    assert isinstance(dto, TicketMessageDTO)
    assert dto.internal is True


@pytest.fixture()
def sample_appeal() -> AppealDTO:
    return AppealDTO(
        id="apl-1",
        target_type="sanction",
        target_id="san-1",
        user_id="user",
    )


def test_merge_appeal_with_db_updates_meta(sample_appeal: AppealDTO) -> None:
    merged = merge_appeal_with_db(
        sample_appeal,
        {
            "status": "approved",
            "decided_at": dt.datetime(2025, 1, 5, tzinfo=dt.UTC),
            "decided_by": "moderator",
            "decision_reason": "ok",
            "meta": {"history": ["entry"]},
        },
    )
    assert merged.status == "approved"
    assert merged.decided_by == "moderator"
    assert merged.meta["history"] == ["entry"]


def test_build_appeal_decision_includes_db_state() -> None:
    resp = build_appeal_decision(
        "apl-1",
        status="approved",
        decided_at="2025-01-05T12:00:00Z",
        decided_by="moderator",
        db_record={"meta": {"history": []}},
    )
    assert resp["db_state"]["meta"] == {"history": []}


def test_build_list_helpers() -> None:
    assert build_list_response([1, 2], next_cursor="10", extra={"total": 2}) == {
        "items": [1, 2],
        "next_cursor": "10",
        "total": 2,
    }
    assert build_reports_list_response([], next_cursor=None) == {
        "items": [],
        "next_cursor": None,
    }
    assert build_tickets_list_response([], next_cursor="") == {
        "items": [],
        "next_cursor": "",
    }
    assert build_messages_response([], next_cursor=None) == {
        "items": [],
        "next_cursor": None,
    }
    assert build_appeals_list_response([], next_cursor=None) == {
        "items": [],
        "next_cursor": None,
    }


def test_build_ai_rule_helpers() -> None:
    rule = AIRuleDTO(
        id="air-1",
        category="abuse",
        thresholds={},
        actions={},
        enabled=True,
    )
    assert build_rules_list_response([rule], next_cursor="2")["items"] == [rule]
    history = {"rule_id": "air-1"}
    assert build_history_response([history], next_cursor=None) == {
        "items": [history],
        "next_cursor": None,
    }
    resp = build_test_response(
        payload={"score": 0.5},
        labels=["spam"],
        scores={"spam": 0.5},
        decision="flag",
        rule=rule,
    )
    assert resp["decision"] == "flag"
    assert resp["rule"] == rule

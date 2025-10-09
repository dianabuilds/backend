from __future__ import annotations

from datetime import UTC, datetime, timedelta
from typing import cast

import pytest

from ..application import factories
from ..application.service import PlatformModerationService
from ..domain.dtos import (
    ContentStatus,
    ContentType,
    ReportStatus,
    SanctionStatus,
    SanctionType,
    TicketPriority,
    TicketStatus,
)

TestData = dict[str, dict[str, str]]


class _ServiceWithTestData(PlatformModerationService):
    test_data: TestData


@pytest.fixture
def moderation_service() -> PlatformModerationService:
    service = cast(_ServiceWithTestData, PlatformModerationService(seed_demo=False))
    test_data = _build_dataset(service)
    service.test_data = test_data
    return service


@pytest.fixture
def moderation_data(
    moderation_service: PlatformModerationService,
) -> TestData:
    service = cast(_ServiceWithTestData, moderation_service)
    return service.test_data


def _build_dataset(service: PlatformModerationService) -> TestData:

    now = datetime(2025, 10, 4, 12, tzinfo=UTC)
    service._now = lambda: now  # type: ignore[method-assign]

    alice = factories.create_user(
        service,
        user_id="user-alice",
        username="alice",
        email="alice@example.com",
        roles=["User"],
        status="active",
        registered_at=now - timedelta(days=120),
        last_seen_at=now - timedelta(hours=2),
    )
    bob = factories.create_user(
        service,
        user_id="user-bob",
        username="bob",
        email="bob@example.com",
        roles=["User"],
        status="active",
        registered_at=now - timedelta(days=200),
        last_seen_at=now - timedelta(hours=1),
    )
    moderator = factories.create_user(
        service,
        user_id="mod-lena",
        username="lena",
        email="lena@example.com",
        roles=["Moderator"],
        status="active",
        registered_at=now - timedelta(days=400),
        last_seen_at=now - timedelta(minutes=5),
    )

    warn = factories.create_sanction(
        service,
        bob,
        stype=SanctionType.warning,
        status=SanctionStatus.active,
        reason="too many spam posts",
        issued_by="mod-lena",
        issued_at=now - timedelta(days=3),
        starts_at=now - timedelta(days=3),
        ends_at=now - timedelta(days=2),
        meta={"severity": "medium"},
    )
    ban = factories.create_sanction(
        service,
        bob,
        stype=SanctionType.ban,
        status=SanctionStatus.active,
        reason="repeated violations",
        issued_by="mod-lena",
        issued_at=now - timedelta(hours=6),
        starts_at=now - timedelta(hours=6),
        ends_at=None,
        meta={"source": "manual"},
    )

    content_pending = factories.create_content(
        service,
        content_id="content-1",
        content_type=ContentType.node,
        author_id=alice.id,
        created_at=now - timedelta(hours=5),
        preview="Buy cheap crystals",
        ai_labels=["spam"],
        status=ContentStatus.pending,
        meta={"language": "en"},
    )
    content_pending.moderation_history.append(
        {
            "actor": "ai-moderator",
            "action": "flag",
            "decided_at": service._iso(now - timedelta(hours=4)),
            "reason": "High spam probability",
        }
    )

    content_resolved = factories.create_content(
        service,
        content_id="content-2",
        content_type=ContentType.comment,
        author_id=bob.id,
        created_at=now - timedelta(days=2),
        preview="Thanks for the update",
        ai_labels=["neutral"],
        status=ContentStatus.resolved,
    )
    content_resolved.moderation_history.append(
        {
            "actor": "moderator:lena",
            "action": "keep",
            "decided_at": service._iso(now - timedelta(days=1, hours=3)),
            "reason": "No violation",
        }
    )

    content_clean = factories.create_content(
        service,
        content_id="content-3",
        content_type=ContentType.node,
        author_id=alice.id,
        created_at=now - timedelta(hours=1),
        preview="Morning photo",
        ai_labels=["photo"],
        status=ContentStatus.pending,
    )

    report_open = factories.create_report(
        service,
        content=content_pending,
        reporter_id=bob.id,
        category="spam",
        text="Looks promotional",
        status=ReportStatus.new,
        created_at=now - timedelta(hours=4),
        source="user",
    )
    report_resolved = factories.create_report(
        service,
        content=content_resolved,
        reporter_id=alice.id,
        category="abuse",
        text="",
        status=ReportStatus.resolved,
        created_at=now - timedelta(days=3),
        source="ai",
    )
    report_resolved.resolved_at = now - timedelta(days=2, hours=12)
    report_resolved.decision = "keep"

    ticket_main = factories.create_ticket(
        service,
        title="Unban request",
        author_id=bob.id,
        priority=TicketPriority.high,
        assignee_id=moderator.id,
        status=TicketStatus.progress,
        created_at=now - timedelta(hours=8),
    )
    message_first = factories.create_ticket_message(
        service,
        ticket_main,
        author_id=bob.id,
        text="Please review my case",
        created_at=now - timedelta(hours=7),
    )
    factories.create_ticket_message(
        service,
        ticket_main,
        author_id=moderator.id,
        text="Investigating",
        created_at=now - timedelta(hours=6),
    )
    ticket_main.unread_count = 1

    ticket_waiting = factories.create_ticket(
        service,
        title="Feature question",
        author_id=alice.id,
        priority=TicketPriority.low,
        assignee_id=None,
        status=TicketStatus.waiting,
        created_at=now - timedelta(days=1),
    )

    appeal_pending = factories.create_appeal(
        service,
        sanction=ban,
        user_id=bob.id,
        text="I have fixed the issues",
        status="pending",
        created_at=now - timedelta(hours=2),
    )

    rule = factories.create_ai_rule(
        service,
        category="spam",
        thresholds={"spam": 0.8},
        actions={"auto_hide": True},
        enabled=True,
        updated_by="mod-lena",
        description="Hide spam when score >= 0.8",
        updated_at=now - timedelta(days=1),
    )

    return {
        "users": {"alice": alice.id, "bob": bob.id, "moderator": moderator.id},
        "content": {
            "pending": content_pending.id,
            "resolved": content_resolved.id,
            "clean": content_clean.id,
        },
        "reports": {"open": report_open.id, "resolved": report_resolved.id},
        "sanctions": {"warn": warn.id, "ban": ban.id},
        "tickets": {"main": ticket_main.id, "waiting": ticket_waiting.id},
        "messages": {"first": message_first.id},
        "appeals": {"pending": appeal_pending.id},
        "ai_rules": {"spam": rule.id},
    }

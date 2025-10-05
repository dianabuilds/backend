from __future__ import annotations

from datetime import timedelta
from typing import TYPE_CHECKING

from ..domain.dtos import (
    ContentStatus,
    ContentType,
    ReportStatus,
    SanctionStatus,
    SanctionType,
    TicketPriority,
    TicketStatus,
)
from . import factories as _factories

if TYPE_CHECKING:  # pragma: no cover
    from .service import PlatformModerationService


def seed_demo(service: PlatformModerationService) -> None:
    """Populate in-memory state with demo data for development."""
    now = service._now()
    alice = _factories.create_user(
        service,
        user_id="u-100",
        username="alice",
        email="alice@example.com",
        roles=["User", "Moderator"],
        status="active",
        registered_at=now - timedelta(days=220),
        last_seen_at=now - timedelta(minutes=5),
        meta={"display_name": "Alice Wonderland"},
    )
    bob = _factories.create_user(
        service,
        user_id="u-101",
        username="bob",
        email="bob@example.com",
        roles=["User"],
        status="banned",
        registered_at=now - timedelta(days=420),
        last_seen_at=now - timedelta(days=60),
        meta={"display_name": "Bob Builder"},
    )
    charlie = _factories.create_user(
        service,
        user_id="u-102",
        username="charlie",
        email="charlie@example.com",
        roles=["User", "Editor"],
        status="active",
        registered_at=now - timedelta(days=180),
        last_seen_at=now - timedelta(hours=1),
        meta={"display_name": "Charlie"},
    )
    _factories.create_user(
        service,
        user_id="u-103",
        username="daria",
        email="daria@example.com",
        roles=["Admin"],
        status="active",
        registered_at=now - timedelta(days=500),
        last_seen_at=now - timedelta(minutes=15),
        meta={"display_name": "Daria"},
    )

    _factories.create_note(
        service,
        alice,
        text="Be careful with NSFW tags.",
        author_id="moderator:kate",
        author_name="Kate",
    )
    _factories.create_note(
        service,
        bob,
        text="Repeated ban - keep under watch.",
        author_id="moderator:lynx",
        author_name="Lynx",
        pinned=True,
    )

    _factories.create_sanction(
        service,
        alice,
        stype=SanctionType.mute,
        status=SanctionStatus.expired,
        reason="Spam links",
        issued_by="moderator:kate",
        issued_at=now - timedelta(days=30),
        starts_at=now - timedelta(days=30),
        ends_at=now - timedelta(days=23),
    )
    ban = _factories.create_sanction(
        service,
        bob,
        stype=SanctionType.ban,
        status=SanctionStatus.active,
        reason="Fraudulent activity",
        issued_by="moderator:lynx",
        issued_at=now - timedelta(days=2),
        starts_at=now - timedelta(days=2),
        ends_at=now + timedelta(days=5),
        evidence=["https://cdn.example/evidence/bob.png"],
    )

    content1 = _factories.create_content(
        service,
        content_id="cnt-100",
        content_type=ContentType.node,
        author_id=bob.id,
        created_at=now - timedelta(hours=5),
        preview="Guide to free gems",
        ai_labels=["spam", "scam"],
        status=ContentStatus.pending,
        meta={"queue": "nodes"},
    )
    content2 = _factories.create_content(
        service,
        content_id="cnt-101",
        content_type=ContentType.comment,
        author_id=alice.id,
        created_at=now - timedelta(hours=8),
        preview="I totally agree!",
        ai_labels=["positive"],
        status=ContentStatus.resolved,
        meta={"queue": "comments"},
    )

    _factories.create_report(
        service,
        content=content1,
        reporter_id=charlie.id,
        category="spam",
        text="Looks like a scam",
        created_at=now - timedelta(hours=4, minutes=20),
        source="user",
    )
    _factories.create_report(
        service,
        content=content1,
        reporter_id=alice.id,
        category="hate",
        text="Contains slurs",
        status=ReportStatus.valid,
        created_at=now - timedelta(hours=3, minutes=45),
        source="ai",
        notes="Auto classified by AI",
    )
    _factories.create_report(
        service,
        content=content2,
        reporter_id=bob.id,
        category="abuse",
        text="Personal attack",
        status=ReportStatus.invalid,
        created_at=now - timedelta(hours=2),
        source="user",
    )

    ticket1 = _factories.create_ticket(
        service,
        title="User appeal follow-up",
        author_id=bob.id,
        priority=TicketPriority.high,
        assignee_id="moderator:lynx",
        status=TicketStatus.progress,
        created_at=now - timedelta(hours=6),
    )
    _factories.create_ticket_message(
        service,
        ticket1,
        author_id=bob.id,
        author_name="bob",
        text="Please review my case",
        created_at=now - timedelta(hours=6),
    )
    _factories.create_ticket_message(
        service,
        ticket1,
        author_id="moderator:lynx",
        author_name="Lynx",
        text="We are looking into it.",
        created_at=now - timedelta(hours=5, minutes=30),
    )
    ticket1.unread_count = 0

    ticket2 = _factories.create_ticket(
        service,
        title="Content review request",
        author_id=charlie.id,
        priority=TicketPriority.normal,
        assignee_id="moderator:kate",
        status=TicketStatus.waiting,
        created_at=now - timedelta(days=1, hours=2),
    )
    _factories.create_ticket_message(
        service,
        ticket2,
        author_id=charlie.id,
        author_name="charlie",
        text="Need clarification on policy",
        created_at=now - timedelta(days=1, hours=2),
    )
    ticket2.unread_count = 1

    _factories.create_appeal(
        service,
        sanction=ban,
        user_id=bob.id,
        text="I was hacked",
        status="pending",
        created_at=now - timedelta(days=1),
    )

    rule1 = _factories.create_ai_rule(
        service,
        category="spam",
        thresholds={"spam": 0.85},
        actions={"auto_hide": True, "escalate": False},
        enabled=True,
        updated_by="admin:vera",
        description="Hide content when spam probability >= 0.85",
    )
    _factories.create_ai_rule(
        service,
        category="hate",
        thresholds={"hate": 0.7},
        actions={"auto_flag": True, "notify": True},
        enabled=True,
        updated_by="admin:vera",
        description="Escalate hate speech automatically",
    )

    content1.moderation_history.append(
        {
            "actor": "ai-moderator",
            "action": "flag",
            "decided_at": service._iso(now - timedelta(hours=4)),
            "reason": "High spam probability",
        }
    )
    content2.moderation_history.append(
        {
            "actor": "moderator:kate",
            "action": "keep",
            "decided_at": service._iso(now - timedelta(hours=6)),
            "reason": "No violation",
        }
    )
    rule1.history.append(
        {
            "updated_at": service._iso(now - timedelta(hours=12)),
            "updated_by": "admin:vera",
            "changes": {"description": "Initial rollout"},
        }
    )

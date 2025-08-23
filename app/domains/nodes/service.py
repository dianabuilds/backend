from __future__ import annotations

from uuid import UUID

from app.domains.system.events import (
    ContentArchived,
    ContentPublished,
    ContentUpdated,
    get_event_bus,
)
from app.schemas.node_common import ContentStatus

ALLOWED_TRANSITIONS: dict[ContentStatus, set[ContentStatus]] = {
    ContentStatus.draft: {ContentStatus.in_review},
    ContentStatus.in_review: {ContentStatus.published},
    ContentStatus.published: set(),
    ContentStatus.archived: set(),
}


def validate_transition(current: ContentStatus, new: ContentStatus) -> None:
    """Validate that status transition is allowed."""
    if new == current:
        return
    allowed = ALLOWED_TRANSITIONS.get(current, set())
    if new not in allowed:
        raise ValueError(f"Invalid transition {current} -> {new}")


async def publish_content(content_id: UUID, slug: str, author_id: UUID) -> None:
    """Publish content and emit domain event."""
    bus = get_event_bus()
    await bus.publish(
        ContentPublished(content_id=content_id, slug=slug, author_id=author_id)
    )


async def update_content(content_id: UUID, slug: str, author_id: UUID) -> None:
    """Update content and emit domain event."""
    bus = get_event_bus()
    await bus.publish(
        ContentUpdated(content_id=content_id, slug=slug, author_id=author_id)
    )


async def archive_content(content_id: UUID, slug: str, author_id: UUID) -> None:
    """Archive content and emit domain event."""
    bus = get_event_bus()
    await bus.publish(
        ContentArchived(content_id=content_id, slug=slug, author_id=author_id)
    )

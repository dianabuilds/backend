from __future__ import annotations

from uuid import UUID

from app.domains.system.events import (
    ContentArchived,
    ContentPublished,
    ContentUpdated,
    get_event_bus,
)


async def publish_content(content_id: UUID, slug: str, author_id: UUID) -> None:
    """Publish content and emit domain event."""
    bus = get_event_bus()
    await bus.publish(ContentPublished(content_id=content_id, slug=slug, author_id=author_id))


async def update_content(content_id: UUID, slug: str, author_id: UUID) -> None:
    """Update content and emit domain event."""
    bus = get_event_bus()
    await bus.publish(ContentUpdated(content_id=content_id, slug=slug, author_id=author_id))


async def archive_content(content_id: UUID, slug: str, author_id: UUID) -> None:
    """Archive content and emit domain event."""
    bus = get_event_bus()
    await bus.publish(ContentArchived(content_id=content_id, slug=slug, author_id=author_id))

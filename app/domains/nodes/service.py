from __future__ import annotations

from uuid import UUID

from app.domains.system.events import (
    NodeArchived,
    NodePublished,
    NodeUpdated,
    get_event_bus,
)
from app.schemas.nodes_common import Status

ALLOWED_TRANSITIONS: dict[Status, set[Status]] = {
    Status.draft: {Status.in_review},
    Status.in_review: {Status.published},
    Status.published: set(),
    Status.archived: set(),
}


def validate_transition(current: Status, new: Status) -> None:
    """Validate that status transition is allowed."""
    if new == current:
        return
    allowed = ALLOWED_TRANSITIONS.get(current, set())
    if new not in allowed:
        raise ValueError(f"Invalid transition {current} -> {new}")


async def publish_content(node_id: UUID, slug: str, author_id: UUID) -> None:
    """Publish node and emit domain event."""
    bus = get_event_bus()
    await bus.publish(
        NodePublished(node_id=node_id, slug=slug, author_id=author_id)
    )


async def update_content(node_id: UUID, slug: str, author_id: UUID) -> None:
    """Update node and emit domain event."""
    bus = get_event_bus()
    await bus.publish(
        NodeUpdated(node_id=node_id, slug=slug, author_id=author_id)
    )


async def archive_content(node_id: UUID, slug: str, author_id: UUID) -> None:
    """Archive node and emit domain event."""
    bus = get_event_bus()
    await bus.publish(
        NodeArchived(node_id=node_id, slug=slug, author_id=author_id)
    )

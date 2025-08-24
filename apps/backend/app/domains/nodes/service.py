from __future__ import annotations

from typing import Any
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from app.schemas.nodes_common import Status
from app.domains.notifications.application.ports.notifications import (
    INotificationPort,
)
from app.domains.telemetry.application.event_metrics_facade import event_metrics

from .dao import NodePatchDAO

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


async def publish_content(
    node_id: UUID,
    slug: str,
    author_id: UUID,
    *,
    workspace_id: UUID,
    notifier: INotificationPort | None = None,
) -> None:
    """Publish node and emit domain event."""
    from app.domains.system.events import NodePublished, get_event_bus

    bus = get_event_bus()
    await bus.publish(
        NodePublished(node_id=node_id, slug=slug, author_id=author_id)
    )
    event_metrics.inc("publish", str(workspace_id))
    if notifier:
        try:
            await notifier.notify(
                "publish",
                author_id,
                workspace_id=workspace_id,
                title="Content published",
                message=slug,
            )
        except Exception:
            pass


async def update_content(node_id: UUID, slug: str, author_id: UUID) -> None:
    """Update node and emit domain event."""
    from app.domains.system.events import NodeUpdated, get_event_bus

    bus = get_event_bus()
    await bus.publish(
        NodeUpdated(node_id=node_id, slug=slug, author_id=author_id)
    )


async def archive_content(node_id: UUID, slug: str, author_id: UUID) -> None:
    """Archive node and emit domain event."""
    from app.domains.system.events import NodeArchived, get_event_bus

    bus = get_event_bus()
    await bus.publish(
        NodeArchived(node_id=node_id, slug=slug, author_id=author_id)
    )


class NodePatchService:
    """Persist node patches for later processing.

    Patches recorded through this service are immediately marked as reverted so
    that they do not affect node data when retrieved via the overlay mechanism.
    """

    @staticmethod
    async def record(
        db: AsyncSession,
        *,
        node_id: UUID,
        data: dict[str, Any],
        actor_id: UUID | None = None,
    ) -> None:
        patch = await NodePatchDAO.create(
            db,
            node_id=node_id,
            data=data,
            created_by_user_id=actor_id,
        )
        # Mark patch as reverted so it won't be applied as a hotfix overlay.
        patch.reverted_at = patch.created_at
        await db.flush()

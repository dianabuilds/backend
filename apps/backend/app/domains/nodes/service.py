from __future__ import annotations

from typing import Any
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.preview import PreviewContext
from app.domains.notifications.application.ports.notifications import (
    INotificationPort,
)
from app.domains.system.events import (
    NodeArchived,
    NodePublished,
    NodeUpdated,
    get_event_bus,
)
from app.schemas.nodes_common import Status

from .dao import NodePatchDAO

ALLOWED_TRANSITIONS: dict[Status, set[Status]] = {
    # Разрешаем публиковать напрямую из черновика, чтобы админ мог сразу публиковать
    Status.draft: {Status.in_review, Status.published},
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
    node_id: int,
    slug: str,
    author_id: UUID,
    *,
    workspace_id: UUID,
    notifier: INotificationPort | None = None,
    preview: PreviewContext | None = None,
) -> None:
    """Publish node and emit domain event."""
    bus = get_event_bus()
    await bus.publish(
        NodePublished(
            node_id=node_id,
            slug=slug,
            author_id=author_id,
            workspace_id=workspace_id,
        )
    )
    if notifier:
        try:
            await notifier.notify(
                "publish",
                author_id,
                account_id=workspace_id,
                title="Content published",
                message=slug,
                preview=preview,
            )
        except Exception:
            pass


async def update_content(
    node_id: int,
    slug: str,
    author_id: UUID,
    *,
    workspace_id: UUID | None = None,
) -> None:
    """Update node and emit domain event."""
    bus = get_event_bus()
    await bus.publish(
        NodeUpdated(
            node_id=node_id,
            slug=slug,
            author_id=author_id,
            workspace_id=workspace_id,
        )
    )


async def archive_content(
    node_id: int,
    slug: str,
    author_id: UUID,
    *,
    workspace_id: UUID | None = None,
) -> None:
    """Archive node and emit domain event."""
    bus = get_event_bus()
    await bus.publish(
        NodeArchived(
            node_id=node_id,
            slug=slug,
            author_id=author_id,
            workspace_id=workspace_id,
        )
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
        node_id: int,
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

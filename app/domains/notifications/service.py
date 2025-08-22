from __future__ import annotations

from uuid import UUID

from app.domains.system.events import (
    ContentArchived,
    ContentPublished,
    ContentUpdated,
    get_event_bus,
)
from app.domains.notifications.infrastructure.models.campaign_models import (
    CampaignStatus,
    NotificationCampaign,
)
from app.core.db.session import db_session


async def _create_campaign(title: str, message: str, author_id: UUID) -> None:
    async with db_session() as session:
        camp = NotificationCampaign(
            title=title,
            message=message,
            status=CampaignStatus.draft,
            created_by=author_id,
        )
        session.add(camp)
        await session.commit()


async def _on_published(event: ContentPublished) -> None:
    await _create_campaign(
        title=f"Content published: {event.slug}",
        message=f"{event.slug} was published",
        author_id=event.author_id,
    )


async def _on_updated(event: ContentUpdated) -> None:
    await _create_campaign(
        title=f"Content updated: {event.slug}",
        message=f"{event.slug} was updated",
        author_id=event.author_id,
    )


async def _on_archived(event: ContentArchived) -> None:
    await _create_campaign(
        title=f"Content archived: {event.slug}",
        message=f"{event.slug} was archived",
        author_id=event.author_id,
    )


_registered = False


def register_listeners() -> None:
    global _registered
    if _registered:
        return
    bus = get_event_bus()
    bus.subscribe(ContentPublished, _on_published)
    bus.subscribe(ContentUpdated, _on_updated)
    bus.subscribe(ContentArchived, _on_archived)
    _registered = True


# Register on import
register_listeners()

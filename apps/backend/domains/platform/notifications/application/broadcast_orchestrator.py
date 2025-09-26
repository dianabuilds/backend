from __future__ import annotations

import logging
from dataclasses import dataclass
from datetime import UTC, datetime

from domains.platform.notifications.application.audience_resolver import (
    AudienceResolutionError,
    BroadcastAudienceResolver,
)
from domains.platform.notifications.application.delivery_service import (
    DeliveryService,
    NotificationEvent,
)
from domains.platform.notifications.application.template_service import (
    TemplateService,
)
from domains.platform.notifications.domain.broadcast import (
    Broadcast,
    BroadcastStatus,
)
from domains.platform.notifications.ports import BroadcastRepo

DEFAULT_TOPIC_KEY = "marketing.campaign"
DEFAULT_CHANNEL_KEY = "broadcasts"


@dataclass(frozen=True)
class BroadcastDeliverySummary:
    broadcast_id: str
    status: BroadcastStatus
    total: int
    sent: int
    failed: int


class BroadcastOrchestrator:
    """Coordinates broadcast delivery lifecycle."""

    def __init__(
        self,
        *,
        repo: BroadcastRepo,
        delivery: DeliveryService,
        audience_resolver: BroadcastAudienceResolver,
        template_service: TemplateService | None = None,
        topic_key: str = DEFAULT_TOPIC_KEY,
        channel_key: str = DEFAULT_CHANNEL_KEY,
        logger: logging.Logger | None = None,
    ) -> None:
        self._repo = repo
        self._delivery = delivery
        self._resolver = audience_resolver
        self._templates = template_service
        self._topic_key = topic_key
        self._channel_key = channel_key
        self._log = logger or logging.getLogger(__name__)

    async def process_due(
        self,
        *,
        limit: int = 10,
        now: datetime | None = None,
    ) -> list[BroadcastDeliverySummary]:
        moment = now or datetime.now(UTC)
        claimed = await self._repo.claim_due(moment, limit)
        summaries: list[BroadcastDeliverySummary] = []
        for broadcast in claimed:
            summary = await self._process_claimed(broadcast)
            if summary is not None:
                summaries.append(summary)
        return summaries

    async def process_one(
        self,
        broadcast_id: str,
        *,
        now: datetime | None = None,
    ) -> BroadcastDeliverySummary | None:
        moment = now or datetime.now(UTC)
        claimed = await self._repo.claim(broadcast_id, now=moment)
        if claimed is None or claimed.status is not BroadcastStatus.SENDING:
            return None
        return await self._process_claimed(claimed)

    async def _process_claimed(
        self,
        broadcast: Broadcast,
    ) -> BroadcastDeliverySummary | None:
        template_slug: str | None = None
        template_locale: str | None = None
        if broadcast.template_id and self._templates is not None:
            try:
                template = await self._templates.get(broadcast.template_id)
            except Exception as exc:  # pragma: no cover - defensive
                self._log.exception(
                    "failed to load broadcast template %s",
                    broadcast.template_id,
                    exc_info=exc,
                )
                template = None
            if template is None:
                await self._repo.update_status(
                    broadcast.id,
                    status=BroadcastStatus.FAILED,
                    finished_at=datetime.now(UTC),
                    total=0,
                    sent=0,
                    failed=0,
                )
                return BroadcastDeliverySummary(
                    broadcast_id=broadcast.id,
                    status=BroadcastStatus.FAILED,
                    total=0,
                    sent=0,
                    failed=0,
                )
            template_slug = template.slug
            template_locale = template.locale

        total = 0
        sent = 0
        failed = 0

        try:
            async for batch in self._resolver.iter_user_ids(broadcast.audience):
                for user_id in batch:
                    total += 1
                    event = self._build_event(
                        broadcast,
                        user_id=user_id,
                        template_slug=template_slug,
                        template_locale=template_locale,
                    )
                    try:
                        result = await self._delivery.deliver_to_inbox(event)
                    except Exception as exc:  # pragma: no cover - defensive
                        failed += 1
                        self._log.exception(
                            "broadcast %s delivery failed for user %s",
                            broadcast.id,
                            user_id,
                            exc_info=exc,
                        )
                        continue
                    if result:
                        sent += 1
        except AudienceResolutionError as exc:
            self._log.error("broadcast %s audience resolution failed: %s", broadcast.id, exc)
            finished = datetime.now(UTC)
            await self._repo.update_status(
                broadcast.id,
                status=BroadcastStatus.FAILED,
                finished_at=finished,
                total=total,
                sent=sent,
                failed=failed if failed else total,
            )
            return BroadcastDeliverySummary(
                broadcast_id=broadcast.id,
                status=BroadcastStatus.FAILED,
                total=total,
                sent=sent,
                failed=failed if failed else total,
            )

        finished_at = datetime.now(UTC)
        status = BroadcastStatus.SENT if failed == 0 else BroadcastStatus.FAILED
        summary = BroadcastDeliverySummary(
            broadcast_id=broadcast.id,
            status=status,
            total=total,
            sent=sent,
            failed=failed,
        )
        await self._repo.update_status(
            broadcast.id,
            status=status,
            finished_at=finished_at,
            total=total,
            sent=sent,
            failed=failed,
        )
        return summary

    def _build_event(
        self,
        broadcast: Broadcast,
        *,
        user_id: str,
        template_slug: str | None,
        template_locale: str | None,
    ) -> NotificationEvent:
        return NotificationEvent(
            topic=self._topic_key,
            user_id=user_id,
            title=broadcast.title,
            body=broadcast.body,
            type="broadcast",
            priority="normal",
            meta={"broadcast_id": broadcast.id},
            context={"broadcast_id": broadcast.id},
            template_slug=template_slug,
            template_locale=template_locale,
            is_preview=False,
            channel_key=self._channel_key,
            event_id=f"broadcast:{broadcast.id}:{user_id}",
        )


__all__ = ["BroadcastDeliverySummary", "BroadcastOrchestrator"]

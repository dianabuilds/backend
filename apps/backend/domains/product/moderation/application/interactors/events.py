from __future__ import annotations

import logging
import time
from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from typing import Any

from domains.platform.events.application.publisher import OutboxError, OutboxPublisher

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class ModerationEvent:
    name: str
    payload: Mapping[str, Any]

    # Optional metadata for logging
    case_id: str | None = None


class ModerationEventPublisher:
    """Facade that wraps OutboxPublisher with consistent logging."""

    def __init__(
        self,
        outbox: OutboxPublisher | None,
        *,
        expected_errors: Sequence[type[Exception]] | None = None,
    ) -> None:
        self._outbox = outbox
        self._expected_errors: tuple[type[Exception], ...] = tuple(
            expected_errors or ()
        )

    def publish(self, event: ModerationEvent) -> None:
        if self._outbox is None:
            logger.debug("moderation_outbox_skipped", extra={"event": event.name})
            return
        extra: dict[str, Any] = {"event": event.name}
        if event.case_id:
            extra["case_id"] = event.case_id
        started = time.perf_counter()
        try:
            self._outbox.publish(event.name, dict(event.payload))
        except self._expected_errors as exc:  # type: ignore[misc]
            logger.warning(
                "moderation_outbox_publish_failed", extra=extra, exc_info=exc
            )
            return
        except Exception as exc:  # pragma: no cover - unexpected failure
            logger.exception(
                "moderation_outbox_publish_unexpected", extra=extra, exc_info=exc
            )
            raise OutboxError(
                "moderation_outbox_publish_unexpected", topic=event.name
            ) from exc
        duration_ms = (time.perf_counter() - started) * 1000
        logger.debug(
            "moderation_outbox_published",
            extra={**extra, "duration_ms": round(duration_ms, 2)},
        )


__all__ = ["ModerationEvent", "ModerationEventPublisher"]

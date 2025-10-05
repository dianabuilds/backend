from __future__ import annotations

import logging
from collections.abc import Mapping
from typing import Any

from domains.platform.flags.application.service import FlagService

logger = logging.getLogger(__name__)


class DeliveryFlagEvaluator:
    """Async cache around flag evaluation used by delivery flows."""

    def __init__(self, service: FlagService | None, context: Mapping[str, Any]) -> None:
        self._service = service
        self._context = dict(context or {})
        self._cache: dict[str, bool] = {}

    async def is_enabled(self, slug: str | None, *, fallback: bool = True) -> bool:
        if not slug:
            return True
        if self._service is None:
            return fallback
        if slug in self._cache:
            return self._cache[slug]
        try:
            flag = await self._service.store.get(slug)
        except (RuntimeError, ValueError) as exc:
            logger.warning(
                "delivery_flag_fetch_failed", extra={"slug": slug}, exc_info=exc
            )
            enabled = fallback
        else:
            if flag is None:
                enabled = fallback
            else:
                enabled = bool(self._service._eval_flag(flag, dict(self._context)))
        self._cache[slug] = enabled
        return enabled


__all__ = ["DeliveryFlagEvaluator"]

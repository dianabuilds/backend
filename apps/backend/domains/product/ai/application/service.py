from __future__ import annotations

import logging
import time
from typing import Any

from domains.platform.events.application.publisher import OutboxError
from domains.platform.telemetry.application.facade import (
    LLMCallLabels,
    llm_metrics,
)
from domains.product.ai.application.errors import ProviderError
from domains.product.ai.application.ports import Provider
from domains.product.profile.application.ports import Outbox as ProfileOutbox

try:
    from redis.exceptions import RedisError  # type: ignore[import-untyped]
except ImportError:  # pragma: no cover
    RedisError = Exception  # type: ignore[misc, assignment]


logger = logging.getLogger(__name__)

_OUTBOX_EXPECTED_ERRORS = (ValueError, RuntimeError, RedisError)


class AIService:
    def __init__(self, provider: Provider, outbox: ProfileOutbox | None = None):
        self.provider = provider
        self.outbox = outbox

    def _safe_publish(
        self,
        topic: str,
        payload: dict[str, Any],
        *,
        labels: LLMCallLabels | None = None,
        key: str | None = None,
        context: dict[str, Any] | None = None,
    ) -> None:
        if not self.outbox:
            return
        extra = {"topic": topic}
        if context:
            extra.update(context)
        try:
            self.outbox.publish(topic, payload, key=key)
        except _OUTBOX_EXPECTED_ERRORS as exc:
            logger.warning("ai_outbox_publish_failed", extra=extra, exc_info=exc)
            if labels:
                llm_metrics.inc("outbox_errors", labels, by=1)
        except Exception as exc:  # pragma: no cover - unexpected, escalate
            logger.exception("ai_outbox_publish_unexpected", extra=extra, exc_info=exc)
            raise OutboxError("ai_outbox_publish_unexpected", topic=topic) from exc

    async def generate(
        self,
        prompt: str,
        *,
        model: str | None = None,
        provider: str | None = None,
        model_id: str | None = None,
    ) -> dict[str, Any]:
        provider_name = (
            (
                provider
                or getattr(self.provider, "__class__", type(self.provider)).__name__
            )
            .replace("Provider", "")
            .lower()
        )
        model_name = model or model_id or "default"
        labels = LLMCallLabels(
            provider=provider_name, model=model_name, stage="unknown"
        )
        started_at = time.perf_counter()
        self._safe_publish(
            "ai.generation.started.v1",
            {
                "prompt_len": len(prompt or ""),
                "provider": provider_name,
                "model": model_name,
            },
            labels=labels,
            key=None,
            context={"phase": "start"},
        )
        try:
            text = await self.provider.generate(
                prompt,
                model=model,
                provider=provider,
                model_id=model_id,
            )
        except ProviderError as exc:
            latency_ms = (time.perf_counter() - started_at) * 1000.0
            llm_metrics.inc("errors", labels, by=1)
            llm_metrics.observe_latency(labels, latency_ms)
            logger.warning(
                "ai_provider_generate_failed",
                extra={
                    "provider": provider_name,
                    "model": model_name,
                    "code": exc.code,
                },
                exc_info=exc,
            )
            raise
        latency_ms = (time.perf_counter() - started_at) * 1000.0
        llm_metrics.inc("calls", labels, by=1)
        llm_metrics.observe_latency(labels, latency_ms)
        result_len = len(text or "")
        self._safe_publish(
            "ai.generation.completed.v1",
            {
                "latency_ms": latency_ms,
                "result_len": result_len,
                "provider": provider_name,
                "model": model_name,
            },
            labels=labels,
            key=None,
            context={"phase": "complete"},
        )
        return {"result": text}

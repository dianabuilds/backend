from __future__ import annotations

import time

from apps.backendDDD.domains.platform.telemetry.application.metrics_registry import (
    llm_metrics,
)
from apps.backendDDD.domains.platform.telemetry.ports.llm_metrics_port import (
    LLMCallLabels,
)
from apps.backendDDD.domains.product.ai.application.ports import Provider


class AIService:
    def __init__(self, provider: Provider, outbox: object | None = None):
        self.provider = provider
        self.outbox = outbox

    async def generate(self, prompt: str) -> dict:
        provider_name = (
            getattr(self.provider, "__class__", type(self.provider))
            .__name__.replace("Provider", "")
            .lower()
        )
        model = "default"
        labels = LLMCallLabels(provider=provider_name, model=model, stage="unknown")
        t0 = time.perf_counter()
        try:
            if self.outbox:
                try:
                    self.outbox.publish(
                        "ai.generation.started.v1",
                        {
                            "prompt_len": len(prompt or ""),
                            "provider": provider_name,
                            "model": model,
                        },
                        key=None,
                    )
                except Exception:
                    pass
            text = await self.provider.generate(prompt)
            # metrics
            dt_ms = (time.perf_counter() - t0) * 1000.0
            llm_metrics.inc("calls", labels, by=1)
            llm_metrics.observe_latency(labels, dt_ms)
            if self.outbox:
                try:
                    self.outbox.publish(
                        "ai.generation.completed.v1",
                        {
                            "latency_ms": dt_ms,
                            "result_len": len(text or ""),
                            "provider": provider_name,
                            "model": model,
                        },
                        key=None,
                    )
                except Exception:
                    pass
            return {"result": text}
        except Exception:
            dt_ms = (time.perf_counter() - t0) * 1000.0
            llm_metrics.inc("errors", labels, by=1)
            llm_metrics.observe_latency(labels, dt_ms)
            raise

from __future__ import annotations

# Централизованный импорт сборщика метрик
from app.domains.telemetry.application.worker_metrics_service import (
    worker_metrics,  # noqa: F401
)

__all__ = ["worker_metrics"]

from __future__ import annotations

# Временный фасад: используем legacy-хранилище worker_metrics, чтобы централизовать импорт
from app.services.worker_metrics import worker_metrics  # noqa: F401

__all__ = ["worker_metrics"]

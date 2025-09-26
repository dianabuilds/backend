from __future__ import annotations

import logging
from collections.abc import Awaitable, Callable, Mapping
from dataclasses import dataclass

from packages.core.config import Settings

from .base import Worker

WorkerBuilder = Callable[["WorkerRuntimeContext"], Worker | Awaitable[Worker]]


@dataclass(slots=True)
class WorkerRuntimeContext:
    settings: Settings
    env: Mapping[str, str]
    logger: logging.Logger


_REGISTRY: dict[str, WorkerBuilder] = {}


def register_worker(name: str) -> Callable[[WorkerBuilder], WorkerBuilder]:
    """Register a worker builder under ``name``."""

    def decorator(builder: WorkerBuilder) -> WorkerBuilder:
        if name in _REGISTRY:
            raise ValueError(f"worker '{name}' already registered")
        _REGISTRY[name] = builder
        return builder

    return decorator


def get_worker_builder(name: str) -> WorkerBuilder:
    try:
        return _REGISTRY[name]
    except KeyError as exc:  # pragma: no cover - defensive
        raise KeyError(f"worker '{name}' is not registered") from exc


def list_registered_workers() -> tuple[str, ...]:
    return tuple(sorted(_REGISTRY))


__all__ = [
    "WorkerBuilder",
    "WorkerRuntimeContext",
    "register_worker",
    "get_worker_builder",
    "list_registered_workers",
]

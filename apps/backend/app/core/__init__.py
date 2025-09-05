from __future__ import annotations  # mypy: ignore-errors

import warnings
from importlib import import_module
from types import ModuleType

__all__ = ["cache", "redis_utils", "outbox"]


def _load(name: str) -> ModuleType:
    module = import_module(f"app.providers.{name}")
    warnings.warn(
        f"Deprecated: use app.providers.{name}",
        DeprecationWarning,
        stacklevel=2,
    )
    return module


def __getattr__(name: str) -> ModuleType:
    if name in {"cache", "redis_utils", "outbox"}:
        module = _load(name)
        globals()[name] = module
        return module
    raise AttributeError(name)

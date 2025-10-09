from __future__ import annotations

import sys
from importlib import import_module
from pathlib import Path
from types import ModuleType
from typing import Any

_BASE = Path(__file__).resolve().parent.parent.parent
_BASE_STR = str(_BASE)

__path__ = [_BASE_STR]

if _BASE_STR not in sys.path:
    sys.path.insert(0, _BASE_STR)

__all__ = ("app", "domains", "packages", "workers")


def _load(name: str) -> ModuleType:
    module = import_module(name)
    sys.modules[f"apps.backend.{name}"] = module
    return module


def __getattr__(name: str) -> Any:
    if name in __all__:
        module = sys.modules.get(f"apps.backend.{name}")
        if module is None:
            module = _load(name)
        return module
    raise AttributeError(name)


def __dir__() -> list[str]:
    return sorted(set(__all__) | set(globals()))

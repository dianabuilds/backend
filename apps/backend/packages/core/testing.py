from __future__ import annotations

import os
import sys
from collections.abc import Iterator
from contextlib import contextmanager
from typing import Any

_override: bool | None = None


def _normalize_env(value: Any) -> str:
    if value is None:
        return ""
    try:
        text = str(value).strip().lower()
    except Exception:
        return ""
    return text


def is_test_mode(settings: Any | None = None) -> bool:
    """Return True when the application should operate in test mode.

    The detection prefers an explicit override first, then the provided
    settings object, followed by environment hints. It also watches for
    pytest bootstrapping markers so unit tests automatically run in the
    lightweight configuration without relying on external services.
    """

    global _override
    if _override is not None:
        return _override

    if settings is not None:
        env_value = _normalize_env(getattr(settings, "env", None))
        if env_value == "test":
            return True

    env_value = _normalize_env(os.getenv("APP_ENV"))
    if env_value == "test":
        return True

    generic_env = _normalize_env(os.getenv("ENV"))
    if generic_env == "test":
        return True

    if os.getenv("PYTEST_CURRENT_TEST"):
        return True

    return "pytest" in sys.modules


def set_test_mode(value: bool | None) -> None:
    """Override automatic detection for the current process."""

    global _override
    _override = value


@contextmanager
def override_test_mode(value: bool) -> Iterator[None]:
    """Temporarily force the detected test mode to the provided value."""

    previous = _override
    set_test_mode(value)
    try:
        yield
    finally:
        set_test_mode(previous)


__all__ = ["is_test_mode", "override_test_mode", "set_test_mode"]

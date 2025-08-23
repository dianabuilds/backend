"""Compatibility wrapper for the main logging configuration module.

Historically tests imported :func:`configure_logging` from this module.
The real implementation now lives in ``logging_configuration``.  This
file simply re-exports the function so that external imports continue to
work without modification.
"""

from __future__ import annotations

from typing import Any

from .logging_configuration import configure_logging as _configure_logging


def configure_logging(config: dict[str, Any] | None = None) -> None:  # pragma: no cover - thin wrapper
    """Proxy to :func:`logging_configuration.configure_logging`."""
    _configure_logging(config)


__all__ = ["configure_logging"]


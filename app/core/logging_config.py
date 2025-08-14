"""Minimal logging configuration stub for tests."""
from __future__ import annotations

import logging
from typing import Any


def configure_logging(config: dict[str, Any] | None = None) -> None:
    """Configure standard logging. Existing implementation is minimal."""
    if config:
        logging.config.dictConfig(config)  # type: ignore[attr-defined]
    else:
        logging.basicConfig(level=logging.INFO)

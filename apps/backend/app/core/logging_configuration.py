"""Application logging configuration utilities.

This module exposes :func:`configure_logging` which sets up standard
logging for the application.  The configuration is intentionally minimal
but covers the needs of the tests and the application:

* logs are written to ``stdout`` so they can be captured by tests or
  container runtimes;
* a :class:`RequestContextFilter` from ``app.core.log_filters`` is
  attached so that ``request_id`` and other context variables appear in
  every log record;
* optional JSON formatting via :class:`JSONFormatter` when the
    ``settings.logging.json_logs`` flag is enabled;
* dedicated loggers for ``uvicorn`` with different levels for
  ``uvicorn.access`` and ``uvicorn.error``.

The function is idempotent – calling it multiple times reconfigures the
logging platform without accumulating handlers.
"""

from __future__ import annotations

import logging
import logging.config
import sys
from typing import Any

from app.core.config import settings


def _resolve_format(fmt: str | None = None) -> str:
    """Return log output format, either ``"json"`` or ``"pretty"``.

    The default is derived from ``settings.logging.json_logs`` where ``True``
    results in JSON output.  Passing an explicit ``fmt`` overrides the
    settings allowing callers to switch formats programmatically.
    """

    if fmt is None:
        return "json" if settings.logging.json_logs else "pretty"
    fmt_lower = fmt.lower()
    return "json" if fmt_lower == "json" else "pretty"


def _build_config(fmt: str | None = None) -> dict[str, Any]:
    """Construct a ``logging.config.dictConfig`` compatible dictionary."""

    formatter: dict[str, Any]
    resolved_fmt = _resolve_format(fmt)
    if resolved_fmt == "json":
        formatter = {"()": "app.core.json_formatter.JSONFormatter"}
    else:
        formatter = {
            "format": "%(asctime)s %(levelname)s %(name)s: %(message)s",
            "datefmt": "%Y-%m-%d %H:%M:%S",
        }

    handlers: dict[str, Any] = {
        "console": {
            "class": "logging.StreamHandler",
            "level": settings.logging.level,
            "stream": sys.stdout,
            "formatter": "default",
            "filters": ["request_context"],
        }
    }

    # Optional file handler – not exercised in tests but supported for
    # completeness.
    if settings.logging.file_enabled:
        handlers["file"] = {
            "class": "logging.handlers.RotatingFileHandler",
            "level": settings.logging.level,
            "formatter": "default",
            "filename": settings.logging.file_path,
            "maxBytes": settings.logging.file_rotate_bytes,
            "backupCount": settings.logging.file_backup_count,
            "filters": ["request_context"],
        }

    root_handlers = ["console"]
    if settings.logging.file_enabled:
        root_handlers.append("file")

    config = {
        "version": 1,
        "disable_existing_loggers": False,
        "filters": {
            "request_context": {
                "()": "app.core.log_filters.RequestContextFilter",
                "service": settings.logging.service_name,
            }
        },
        "formatters": {"default": formatter},
        "handlers": handlers,
        "loggers": {
            # Uvicorn's loggers.  Access logs are less noisy than error
            # logs, hence different levels.
            "uvicorn": {
                "handlers": root_handlers,
                "level": settings.logging.level,
                "propagate": False,
            },
            "uvicorn.access": {
                "handlers": root_handlers,
                "level": "INFO",
                "propagate": False,
            },
            "uvicorn.error": {
                "handlers": root_handlers,
                "level": "WARNING",
                "propagate": False,
            },
            # HTTP request logs emitted from ``RequestLoggingMiddleware``.
            "app.http": {
                "handlers": root_handlers,
                "level": settings.logging.request_level,
                "propagate": False,
            },
        },
        "root": {"level": settings.logging.level, "handlers": root_handlers},
    }

    return config


def configure_logging(config: dict[str, Any] | None = None, fmt: str | None = None) -> None:
    """Configure application logging.

    Parameters
    ----------
    config:
        Optional explicit configuration dictionary.  When omitted a
        sensible default configuration based on ``settings.logging`` is
        used.
    """

    if config is None:
        config = _build_config(fmt)

    # ``dictConfig`` replaces existing handlers for the specified
    # loggers.  Clearing root handlers prevents duplicate logs if the
    # function is called multiple times (tests exercise this behaviour).
    root_logger = logging.getLogger()
    for handler in list(root_logger.handlers):
        root_logger.removeHandler(handler)

    logging.config.dictConfig(config)


__all__ = ["configure_logging"]

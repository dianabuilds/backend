from __future__ import annotations

import json
import logging
import logging.config
import os
from typing import Any

from app.kernel.config import settings


def _build_config(fmt: str | None = None) -> dict[str, Any]:
    log_format = fmt or os.getenv("LOG_FORMAT", settings.logging.format)

    if log_format == "json":
        formatter = {
            "()": "app.kernel.json_formatter.JSONFormatter",
        }
    else:
        formatter = {
            "format": "%(asctime)s %(levelname)s %(name)s [req:%(request_id)s user:%(user_id)s] %(message)s",
            "datefmt": "%Y-%m-%dT%H:%M:%S%z",
        }

    handlers = {
        "console": {
            "class": "logging.StreamHandler",
            "formatter": "default",
            "stream": "ext://sys.stdout",
            "filters": ["request_context"],
        }
    }
    root_handlers = ["console"]

    config: dict[str, Any] = {
        "version": 1,
        "disable_existing_loggers": False,
        "filters": {
            "request_context": {
                "()": "app.domains.telemetry.log_filters.RequestContextFilter",
                "service": settings.logging.service_name,
            }
        },
        "formatters": {"default": formatter},
        "handlers": handlers,
        "loggers": {
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
            "app.http": {
                "handlers": root_handlers,
                "level": settings.logging.request_level,
                "propagate": False,
            },
        },
        "root": {
            "level": settings.logging.level,
            "handlers": root_handlers,
            "filters": ["request_context"],
        },
    }

    return config


def configure_logging(config: dict[str, Any] | None = None, fmt: str | None = None) -> None:
    if config is None:
        config = _build_config(fmt)
    root_logger = logging.getLogger()
    for handler in list(root_logger.handlers):
        root_logger.removeHandler(handler)
    logging.config.dictConfig(config)


__all__ = ["configure_logging"]

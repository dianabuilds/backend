from logging.config import dictConfig

from app.core.config import settings


def build_logging_dict() -> dict:
    fmt_readable = (
        "%(asctime)s %(levelname)s %(name)s [%(request_id)s %(user_id)s] %(message)s"
    )
    return {
        "version": 1,
        "disable_existing_loggers": False,
        "filters": {
            "context": {
                "()": "app.core.log_filters.RequestContextFilter",
                "service": settings.logging.service_name,
            }
        },
        "formatters": {
            "readable": {"format": fmt_readable},
            "json": {"()": "app.core.json_formatter.JSONFormatter"},
        },
        "handlers": {
            "console": {
                "class": "logging.StreamHandler",
                "filters": ["context"],
                "formatter": "json" if settings.logging.json else "readable",
            },
            "audit": {
                "class": "app.core.audit_log.AuditLogHandler",
                "level": "INFO",
                "filters": ["context"],
            },
            **(
                {
                    "file": {
                        "class": "logging.handlers.RotatingFileHandler",
                        "filename": settings.logging.file_path,
                        "maxBytes": settings.logging.file_rotate_bytes,
                        "backupCount": settings.logging.file_backup_count,
                        "filters": ["context"],
                        "formatter": "json" if settings.logging.json else "readable",
                    }
                }
                if settings.logging.file_enabled
                else {}
            ),
        },
        "loggers": {
            "uvicorn": {"level": settings.logging.level},
            "uvicorn.error": {"level": settings.logging.level},
            "uvicorn.access": {"level": settings.logging.level},
            "app": {
                "level": settings.logging.level,
                "handlers": [],
                "propagate": True,
            },
        },
        "root": {
            "level": settings.logging.level,
            "handlers": ["console", "audit"]
            + (["file"] if settings.logging.file_enabled else []),
        },
    }


def configure_logging() -> None:
    dictConfig(build_logging_dict())


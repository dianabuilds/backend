from __future__ import annotations

import logging
from dataclasses import dataclass

from sqlalchemy.exc import SQLAlchemyError

from packages.core.config import Settings, load_settings
from packages.core.db import get_async_engine

from .service import PlatformModerationService
from .storage import ModerationStorage

logger = logging.getLogger(__name__)


@dataclass
class ModerationContainer:
    settings: Settings
    service: PlatformModerationService


def build_container(settings: Settings | None = None) -> ModerationContainer:
    cfg = settings or load_settings()
    engine = None
    if getattr(cfg, "database_url", None):
        try:
            engine = get_async_engine("platform-moderation", url=str(cfg.database_url))
        except (SQLAlchemyError, ValueError, TypeError) as exc:
            logger.error("Failed to initialise moderation SQL engine: %s", exc)
            engine = None
        except ImportError as exc:
            logger.warning("SQLAlchemy not available for moderation module: %s", exc)
            engine = None
    storage = ModerationStorage(engine)
    svc = PlatformModerationService(storage=storage, seed_demo=cfg.env != "prod")
    return ModerationContainer(settings=cfg, service=svc)


__all__ = ["ModerationContainer", "build_container"]

from __future__ import annotations

from dataclasses import dataclass

from packages.core.config import Settings, load_settings
from packages.core.db import get_async_engine

from .service import PlatformModerationService
from .storage import ModerationStorage


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
        except Exception:
            engine = None
    storage = ModerationStorage(engine)
    svc = PlatformModerationService(storage=storage, seed_demo=cfg.env != "prod")
    return ModerationContainer(settings=cfg, service=svc)


__all__ = ["ModerationContainer", "build_container"]

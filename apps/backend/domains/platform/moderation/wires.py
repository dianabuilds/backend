from __future__ import annotations

from dataclasses import dataclass

from packages.core.config import Settings, load_settings

from .service import PlatformModerationService


@dataclass
class ModerationContainer:
    settings: Settings
    service: PlatformModerationService


def build_container(settings: Settings | None = None) -> ModerationContainer:
    cfg = settings or load_settings()
    svc = PlatformModerationService()
    return ModerationContainer(settings=cfg, service=svc)


__all__ = ["ModerationContainer", "build_container"]

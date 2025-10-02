from __future__ import annotations

from fastapi import APIRouter

from . import billing, features, notifications, profile, security
from .common import SETTINGS_SCHEMA_TAG

router = APIRouter(prefix="/v1/settings", tags=[SETTINGS_SCHEMA_TAG])
me_router = APIRouter(prefix="/v1/me/settings", tags=[SETTINGS_SCHEMA_TAG])

features.register(router, me_router)
profile.register(router, me_router)
billing.register(router, me_router)
notifications.register(router, me_router)
security.register(router, me_router)

__all__ = ["router", "me_router", "SETTINGS_SCHEMA_TAG"]

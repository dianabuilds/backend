from __future__ import annotations

from fastapi import APIRouter

router = APIRouter()

# Use domain-native routers instead of legacy app.api proxies
from app.domains.quests.api.quests_router import router as quests_router  # noqa: E402
from app.domains.quests.api.admin_validation_router import router as admin_validation_router  # noqa: E402

router.include_router(quests_router)
router.include_router(admin_validation_router)

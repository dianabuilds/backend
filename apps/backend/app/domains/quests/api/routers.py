from __future__ import annotations

from fastapi import APIRouter

# Use domain-native routers instead of legacy app.api proxies
from app.domains.quests.api.admin_validation_router import (
    router as admin_validation_router,
)
from app.domains.quests.api.admin_versions_router import (
    router as admin_versions_router,
)
from app.domains.quests.api.quests_router import router as quests_router
from app.domains.quests.api.versions_router import (
    router as versions_router,
)
from app.domains.quests.api.admin_steps_router import (
    router as admin_steps_router,
    graph_router as admin_steps_graph_router,
)

router = APIRouter()

router.include_router(quests_router)
router.include_router(versions_router)
router.include_router(admin_versions_router)
router.include_router(admin_validation_router)
router.include_router(admin_steps_router)
router.include_router(admin_steps_graph_router)

from __future__ import annotations

from fastapi import APIRouter

# Use domain-native routers instead of legacy app.api proxies
from app.domains.quests.api.admin_router import (
    router as deprecated_admin_router,  # noqa: E402
)
from app.domains.quests.api.admin_validation_router import (
    router as admin_validation_router,  # noqa: E402
)
from app.domains.quests.api.admin_versions_router import (
    router as admin_versions_router,  # noqa: E402
)
from app.domains.quests.api.quests_router import router as quests_router  # noqa: E402
from app.domains.quests.api.versions_router import (
    router as versions_router,  # noqa: E402
)

router = APIRouter()

router.include_router(quests_router)
router.include_router(versions_router)
router.include_router(admin_versions_router)
router.include_router(admin_validation_router)
router.include_router(deprecated_admin_router)

from __future__ import annotations

from fastapi import APIRouter

from app.domains.navigation.api.admin_navigation_router import (
    router as admin_navigation_router,
)
from app.domains.navigation.api.nodes_manage_router import (
    router as nodes_manage_router,
)
from app.domains.navigation.api.nodes_public_router import (
    router as navigation_router,
)
from app.domains.navigation.api.preview_router import (
    router as preview_router,
)

router = APIRouter()

# Aggregate navigation domain routers.
#
# This module used to import legacy routers from ``app.api``. After the
# navigation domain was moved under ``app.domains.navigation`` the old imports
# became invalid which prevented the router from being included during
# application start-up. As a result, endpoints such as ``POST
# /admin/preview/link`` were missing and the admin UI received ``405 Method Not
# Allowed`` when requesting a preview link.
#
# We now import the routers from their new locations to ensure they are
# registered correctly.

router.include_router(navigation_router)
router.include_router(nodes_manage_router)
router.include_router(admin_navigation_router)
router.include_router(preview_router)

__all__ = ["router"]

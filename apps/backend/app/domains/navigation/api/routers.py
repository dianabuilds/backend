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

# Агрегатор доменных роутеров навигации: публичные, управление, админ и превью.
# Наличие здесь preview_router гарантирует, что POST /admin/preview/link доступен.
router = APIRouter()
router.include_router(navigation_router)
router.include_router(nodes_manage_router)
router.include_router(admin_navigation_router)
router.include_router(preview_router)

__all__ = ["router"]

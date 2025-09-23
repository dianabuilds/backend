from . import router as _router
from .ai_rules.http import router as ai_rules_router
from .appeals.http import router as appeals_router
from .content.http import router as content_router
from .overview.http import router as overview_router
from .reports.http import router as reports_router
from .tickets.http import router as tickets_router
from .users.http import router as users_router

router = _router

# Aggregate moderation sub-routers under /api/moderation/*
router.include_router(overview_router)
router.include_router(users_router)
router.include_router(content_router)
router.include_router(reports_router)
router.include_router(tickets_router)
router.include_router(appeals_router)
router.include_router(ai_rules_router)

__all__ = ["router"]

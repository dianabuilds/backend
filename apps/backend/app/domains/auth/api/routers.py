from __future__ import annotations

from fastapi import APIRouter

import app.domains.auth.api.auth_router as auth_router_module
from app.schemas.auth import LoginResponse

router = APIRouter()

router.include_router(auth_router_module.router)

# Для обратной совместимости поддерживаем старый путь /refresh
router.add_api_route(
    "/refresh",
    auth_router_module.refresh,
    methods=["POST"],
    response_model=LoginResponse,
    tags=["auth"],
)

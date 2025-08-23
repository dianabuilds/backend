from __future__ import annotations

from fastapi import APIRouter

router = APIRouter()

# Подключаем доменный роутер авторизации
from app.domains.auth.api.auth_router import router as auth_router  # noqa: E402

router.include_router(auth_router)

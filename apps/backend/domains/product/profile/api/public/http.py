"""HTTP handlers for the public contour of domain product.profile."""

from fastapi import APIRouter

from ..http import register_personal_routes


def make_router() -> APIRouter:
    """Build router exposing только пользовательские эндпоинты профиля."""
    router = APIRouter(prefix="/v1/profile", tags=["profile"])
    register_personal_routes(router)
    return router


# Поддерживаем ленивое переиспользование в register_public и тестах.
router = make_router()


__all__ = ["make_router", "router"]

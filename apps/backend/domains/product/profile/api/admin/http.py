"""HTTP handlers for the admin contour of domain product.profile."""

from fastapi import APIRouter

from ..http import register_admin_routes


def make_router() -> APIRouter:
    """Build router с административными маршрутами профиля."""
    router = APIRouter(prefix="/v1/admin/profile", tags=["admin-profile"])
    register_admin_routes(router)
    return router


# Экспортируем реальный экземпляр для register_admin и unit-тестов.
router = make_router()


__all__ = ["make_router", "router"]

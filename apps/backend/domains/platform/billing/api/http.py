from __future__ import annotations

from fastapi import APIRouter

from .admin import register_admin_routes
from .overview import register_overview_routes
from .public import register_public_routes


def make_router() -> APIRouter:
    router = APIRouter(prefix="/v1/billing", tags=["billing"])
    register_public_routes(router)
    register_admin_routes(router)
    register_overview_routes(router)
    return router

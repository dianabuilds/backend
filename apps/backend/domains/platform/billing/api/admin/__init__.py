from __future__ import annotations

from fastapi import APIRouter

from . import contracts, plans, providers


def register_admin_routes(router: APIRouter) -> None:
    """Подключает административные маршруты биллинга."""
    plans.register(router)
    providers.register(router)
    contracts.register(router)

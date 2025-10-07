from __future__ import annotations

from fastapi import APIRouter

from . import checkout, plans, subscriptions, webhook


def register_public_routes(router: APIRouter) -> None:
    """Подключает публичные маршруты биллинга к переданному роутеру."""
    plans.register(router)
    checkout.register(router)
    subscriptions.register(router)
    webhook.register(router)

"""
Domains.Payments: Manager re-export.

from app.domains.payments.manager import verify_payment, load_active_gateways
"""

from .manager_impl import (
    get_active_subscriptions_stats,
    load_active_gateways,
    verify_payment,
)  # noqa: F401

__all__ = [
    "verify_payment",
    "load_active_gateways",
    "get_active_subscriptions_stats",
]

"""
Payments manager (compat shim).

Deprecated: import from ``app.domains.payments.application.gateways_service``.
This module re-exports the application-layer helpers for backwards
compatibility.
"""

from app.domains.payments.application.gateways_service import (  # noqa: F401
    get_active_subscriptions_stats,
    load_active_gateways,
    verify_payment,
)

__all__ = [
    "verify_payment",
    "load_active_gateways",
    "get_active_subscriptions_stats",
]

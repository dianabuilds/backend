from __future__ import annotations

"""
Payments gateways service (application layer).

This module provides a stable import surface for payment gateway operations.
Historically these helpers lived in ``manager_impl.py``. New code should import
from here; the legacy ``manager.py`` keeps a compat re-export.
"""

from typing import Any, Tuple

from sqlalchemy.ext.asyncio import AsyncSession

# Reuse the existing implementations for now to minimise churn.
# The implementation can be inlined here in a follow-up without
# affecting import sites.
from app.domains.payments.manager_impl import (  # noqa: F401
    get_active_subscriptions_stats,
    load_active_gateways,
)
from app.domains.payments.manager_impl import verify_payment as _verify_payment


async def verify_payment(
    db: AsyncSession, *, amount: int, currency: str | None, token: str, preferred_slug: str | None = None
) -> Tuple[bool, str | None]:
    """Verify a payment using configured gateways.

    Returns a tuple (ok, gateway_slug). The implementation delegates to the
    existing manager logic while exposing an application-layer import path.
    """

    return await _verify_payment(
        db, amount=amount, currency=currency, token=token, preferred_slug=preferred_slug
    )


__all__ = [
    "verify_payment",
    "load_active_gateways",
    "get_active_subscriptions_stats",
]


"""
Domains.Payments: Manager re-export.

from app.domains.payments.manager import verify_payment, load_active_gateways
"""
from .manager_impl import verify_payment, load_active_gateways  # noqa: F401

__all__ = ["verify_payment", "load_active_gateways"]

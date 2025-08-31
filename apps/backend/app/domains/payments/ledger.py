"""
Domains.Payments: Ledger re-export.

from app.domains.payments.ledger import capture_transaction
"""

from .ledger_impl import capture_transaction  # noqa: F401

__all__ = ["capture_transaction"]

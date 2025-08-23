"""
Domains.Payments: Admin API re-export.

from app.domains.payments.api_admin import router
"""
from app.api.admin_payments import router

__all__ = ["router"]

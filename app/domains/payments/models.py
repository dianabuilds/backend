"""
Domains.Payments: Models re-export.

from app.domains.payments.models import PaymentGatewayConfig, PaymentTransaction
"""
from app.domains.payments.infrastructure.models.payment_models import PaymentGatewayConfig
from app.domains.payments.infrastructure.models.payment_models import PaymentTransaction

__all__ = ["PaymentGatewayConfig", "PaymentTransaction"]

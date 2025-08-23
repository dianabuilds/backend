"""
Domains.Premium: Models re-export.

from app.domains.premium.models import SubscriptionPlan, UserSubscription
"""
from app.domains.premium.infrastructure.models.premium_models import SubscriptionPlan, UserSubscription

__all__ = ["SubscriptionPlan", "UserSubscription"]

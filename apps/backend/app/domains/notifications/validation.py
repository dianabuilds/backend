from __future__ import annotations

from app.schemas.notification_rules import NotificationRules

def validate_notification_rules(data: dict[str, object]) -> NotificationRules:
    """Validate workspace notification rules structure."""
    return NotificationRules.model_validate(data)

__all__ = ["validate_notification_rules", "NotificationRules"]

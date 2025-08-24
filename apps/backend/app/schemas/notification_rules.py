from __future__ import annotations

from enum import Enum
from pydantic import BaseModel, ConfigDict, Field, model_validator


class NotificationChannel(str, Enum):
    """Supported notification delivery channels."""

    in_app = "in-app"
    email = "email"
    webhook = "webhook"


class NotificationRules(BaseModel):
    """Workspace notification rules mapped by trigger."""

    achievement: list[NotificationChannel] = Field(default_factory=list)
    publish: list[NotificationChannel] = Field(default_factory=list)

    model_config = ConfigDict(extra="forbid")

    @model_validator(mode="after")
    def _dedupe(self) -> "NotificationRules":
        """Remove duplicate channels per trigger."""
        self.achievement = list(dict.fromkeys(self.achievement))
        self.publish = list(dict.fromkeys(self.publish))
        return self


__all__ = ["NotificationChannel", "NotificationRules"]

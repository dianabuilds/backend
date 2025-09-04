from __future__ import annotations

from datetime import timedelta

from pydantic import BaseModel, Field
from pydantic_settings import SettingsConfigDict


class ModerationSettings(BaseModel):
    """SLA and notification settings for moderation cases."""

    first_response_minutes: int = Field(30, description="Minutes to first response")
    resolution_minutes: int = Field(1440, description="Minutes to resolve a case")
    notify_emails: list[str] = Field(default_factory=list)
    slack_webhook_url: str | None = None

    model_config = SettingsConfigDict(env_prefix="MODERATION_")

    def first_response_delta(self) -> timedelta:
        return timedelta(minutes=self.first_response_minutes)

    def resolution_delta(self) -> timedelta:
        return timedelta(minutes=self.resolution_minutes)

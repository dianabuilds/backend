from __future__ import annotations

from pydantic_settings import BaseSettings, SettingsConfigDict


class FeatureFlags(BaseSettings):
    """Application feature flags."""

    model_config = SettingsConfigDict(env_prefix="FF_", case_sensitive=False)

    profile_enabled: bool = False
    routing_accounts_v2: bool = False


feature_flags = FeatureFlags()

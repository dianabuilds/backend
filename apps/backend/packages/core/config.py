from __future__ import annotations

from typing import Literal

from pydantic import AnyUrl, Field, ValidationError, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_prefix="APP_",
        # Load env from new locations (repo root first), fallback to app dir
        env_file=(
            ".env.local",
            ".env",
            "apps/backend/.env.local",
            "apps/backend/.env",
        ),
        env_file_encoding="utf-8",
        extra="ignore",
    )

    # base
    env: Literal["dev", "test", "prod"] = "dev"
    database_url: AnyUrl = Field(default="postgresql://app:app@localhost:5432/app")
    redis_url: AnyUrl = Field(default="redis://localhost:6379/0")

    # events platform
    event_topics: str = "profile.updated.v1"  # CSV
    event_group: str = "relay"
    event_rate_qps: int = 1000
    event_idempotency_ttl: int = 86400

    # notifications
    notify_topics: str | None = None  # CSV; if None, reuse event_topics
    notify_webhook_url: AnyUrl | None = None

    # SMTP (email notifications)
    smtp_mock: bool = True
    smtp_host: str | None = None
    smtp_port: int | None = 587
    smtp_username: str | None = None
    smtp_password: str | None = None
    smtp_tls: bool = True
    smtp_mail_from: str | None = None
    smtp_mail_from_name: str | None = None

    # auth/iam (stub defaults)
    auth_jwt_secret: str = Field(default="dev-secret-change-me")
    auth_jwt_algorithm: str = Field(default="HS256")
    auth_jwt_expires_min: int = 15
    auth_jwt_refresh_expires_days: int = 7
    auth_csrf_cookie_name: str = Field(default="XSRF-TOKEN")
    auth_csrf_header_name: str = Field(default="X-CSRF-Token")

    # admin guard
    admin_api_key: str | None = None

    # search (in-memory only)
    search_persist_path: str | None = "apps/backend/var/search_index.json"

    # product feature flags (DDD-only)
    referrals_enabled: bool = True
    premium_enabled: bool = True
    achievements_enabled: bool = True
    worlds_enabled: bool = True

    # normalize optional URL envs: empty string -> None
    @field_validator("notify_webhook_url", mode="before")
    @classmethod
    def _empty_url_to_none(cls, v):  # type: ignore[override]
        if v is None:
            return None
        try:
            sv = str(v).strip()
        except Exception:
            return v
        return None if sv == "" else v

    # experimental routers (can be disabled for cutover)
    nodes_enabled: bool = True
    tags_enabled: bool = True
    quests_enabled: bool = True
    navigation_enabled: bool = True
    ai_enabled: bool = True
    moderation_enabled: bool = True


def to_async_dsn(url: AnyUrl) -> str:
    """Convert sync Postgres URL to asyncpg URL for SQLAlchemy Async.

    If already an async URL, returns as-is.
    """
    s = str(url)
    if s.startswith("postgresql+asyncpg://"):
        return s
    if s.startswith("postgresql://"):
        return "postgresql+asyncpg://" + s[len("postgresql://") :]
    return s


def load_settings() -> Settings:
    s = Settings()
    if s.env == "prod":
        # Primitive guard; extend as needed.
        if "localhost" in str(s.database_url):
            raise ValidationError("localhost database in prod", Settings)
    return s

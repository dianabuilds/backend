from __future__ import annotations

import re
from typing import Literal
from urllib.parse import parse_qsl, urlencode, urlparse, urlunparse

from pydantic import AliasChoices, AnyUrl, Field, ValidationError, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_prefix="APP_",
        # Prefer backend-scoped env files first, then repo root fallbacks
        # so that apps/backend/.env can override values from root .env
        env_file=(
            "apps/backend/.env",
            ".env",
        ),
        env_file_encoding="utf-8",
        extra="ignore",
    )

    # base
    env: Literal["dev", "test", "prod"] = "dev"
    database_url: AnyUrl = Field(default="postgresql://app:app@localhost:5432/app")
    redis_url: AnyUrl = Field(default="redis://localhost:6379/0")
    database_allow_remote: bool = Field(
        default=False,
        validation_alias=AliasChoices("DATABASE_ALLOW_REMOTE", "APP_DATABASE_ALLOW_REMOTE"),
    )

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
    auth_bootstrap_login: str | None = None
    auth_bootstrap_password: str | None = None
    auth_bootstrap_role: str = "admin"
    auth_bootstrap_user_id: str = "bootstrap-root"
    cors_origins: str | None = None

    # admin guard
    admin_api_key: str | None = None

    # admin guard

    # admin guard
    admin_api_key: str | None = None

    # search (in-memory only)
    search_persist_path: str | None = "apps/backend/var/search_index.json"

    # product feature flags (DDD-only)
    referrals_enabled: bool = True
    premium_enabled: bool = True
    achievements_enabled: bool = True
    worlds_enabled: bool = True

    # billing/webhook integration
    billing_webhook_secret: str | None = None

    embedding_provider: str | None = Field(
        default=None, validation_alias=AliasChoices("EMBEDDING_PROVIDER", "APP_EMBEDDING_PROVIDER")
    )
    embedding_api_base: str | None = Field(
        default=None, validation_alias=AliasChoices("EMBEDDING_API_BASE", "APP_EMBEDDING_API_BASE")
    )
    embedding_model: str | None = Field(
        default=None, validation_alias=AliasChoices("EMBEDDING_MODEL", "APP_EMBEDDING_MODEL")
    )
    embedding_api_key: str | None = Field(
        default=None, validation_alias=AliasChoices("EMBEDDING_API_KEY", "APP_EMBEDDING_API_KEY")
    )
    embedding_dim: int | None = Field(
        default=None, validation_alias=AliasChoices("EMBEDDING_DIM", "APP_EMBEDDING_DIM")
    )
    embedding_enabled: bool = True
    embedding_timeout: float = Field(default=10.0)
    embedding_connect_timeout: float = Field(default=2.0)
    embedding_retries: int = 3

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
    content_enabled: bool = True
    ai_enabled: bool = True
    moderation_enabled: bool = True


def to_async_dsn(url: AnyUrl) -> str:
    """Convert sync Postgres URL to asyncpg URL for SQLAlchemy Async.

    - If already an async URL, returns as-is.
    - Convert libpq-style `sslmode` to asyncpg-compatible `ssl` flag to avoid
      `TypeError: connect() got an unexpected keyword argument 'sslmode'`.
    """
    s = str(url)
    # Normalize scheme first
    if s.startswith("postgresql+asyncpg://"):
        out = s
    elif s.startswith("postgresql://"):
        out = "postgresql+asyncpg://" + s[len("postgresql://") :]
    else:
        out = s

    # Map/normalize ssl params for asyncpg: remove sslmode always
    try:
        u = urlparse(out)
        raw_pairs = parse_qsl(u.query)
        q: dict[str, str] = {}
        sslmode_val: str | None = None
        ssl_flag: str | None = None
        for key, value in raw_pairs:
            lower_key = key.lower()
            if lower_key == "sslmode":
                sslmode_val = value
                continue
            if lower_key == "ssl" and ssl_flag is None:
                ssl_flag = str(value)
                continue
            q[key] = value
        if sslmode_val is not None:
            mode = str(sslmode_val).strip().lower()
            if mode in ("require", "verify-full", "verify-ca"):
                ssl_flag = "true"
            elif mode in ("disable", "allow", "prefer", "0", "false"):
                ssl_flag = "false"
            else:
                # Unknown value -> default to non-SSL to avoid client errors
                ssl_flag = "false"
        if ssl_flag is not None:
            q["ssl"] = ssl_flag
        new_query = urlencode(q)
        out = urlunparse((u.scheme, u.netloc, u.path, u.params, new_query, u.fragment))
    except Exception:
        # if parsing fails, return as-is
        pass

    # Final guard: strip any lingering sslmode from the full DSN string
    try:
        out = re.sub(
            r"([?&])sslmode=[^&]*(&|$)",
            lambda m: m.group(1) if m.group(2) == "&" else "",
            out,
            flags=re.IGNORECASE,
        )
        # Remove possible trailing '?' or '&'
        out = re.sub(r"[?&]$", "", out)
    except Exception:
        pass
    return out


def load_settings() -> Settings:
    s = Settings()
    if s.env == "prod":
        # Primitive guard; extend as needed.
        if "localhost" in str(s.database_url):
            raise ValidationError("localhost database in prod", Settings)
        if not s.database_allow_remote:
            s.database_allow_remote = True
    return s

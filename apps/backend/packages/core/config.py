from __future__ import annotations

import logging
import re
from typing import Any, Literal, cast
from urllib.parse import parse_qsl, urlencode, urlparse, urlunparse

from pydantic import (
    AliasChoices,
    AnyUrl,
    BaseModel,
    Field,
    SecretStr,
    ValidationError,
    field_validator,
)

TRUTHY_SSL_VALUES = {
    "require",
    "verify-full",
    "verify-ca",
    "allow",
    "prefer",
    "true",
    "1",
    "yes",
    "on",
}
FALSY_SSL_VALUES = {"disable", "false", "0", "no", "off"}

logger = logging.getLogger(__name__)


def _map_ssl_value(value: str | None) -> str:
    if value is None:
        return "true"
    normalized = str(value).strip().lower()
    if normalized in FALSY_SSL_VALUES:
        return "false"
    if normalized in TRUTHY_SSL_VALUES:
        return "true"
    return "true"


def _coerce_async_scheme(url: str) -> str:
    if url.startswith("postgresql+asyncpg://"):
        return url
    if url.startswith("postgresql://"):
        return "postgresql+asyncpg://" + url[len("postgresql://") :]
    return url


def _normalize_async_ssl(url: str) -> str:
    try:
        parsed = urlparse(url)
        raw_pairs = parse_qsl(parsed.query, keep_blank_values=True)
        ssl_value: str | None = None
        filtered: list[tuple[str, str]] = []
        for key, value in raw_pairs:
            lower = key.lower()
            if lower == "sslmode":
                ssl_value = _map_ssl_value(value)
                continue
            if lower == "ssl":
                ssl_value = _map_ssl_value(value)
                continue
            filtered.append((key, value))
        if ssl_value is not None:
            filtered.append(("ssl", ssl_value))
        new_query = urlencode(filtered)
        url = urlunparse(
            (
                parsed.scheme,
                parsed.netloc,
                parsed.path,
                parsed.params,
                new_query,
                parsed.fragment,
            )
        )
    except (ValueError, TypeError) as exc:
        logger.debug("sanitize_async_dsn: parse failed for %s", url, exc_info=exc)
        return url
    try:
        url = re.sub(
            r"([?&])sslmode=[^&]*(&|$)",
            lambda m: m.group(1) if m.group(2) == "&" else "",
            url,
            flags=re.IGNORECASE,
        )
        url = re.sub(r"[?&]$", "", url)
    except re.error as exc:
        logger.debug("sanitize_async_dsn: cleanup failed for %s", url, exc_info=exc)
    return url


def sanitize_async_dsn(url: AnyUrl | str) -> str:
    return _normalize_async_ssl(_coerce_async_scheme(str(url)))


from pydantic_settings import BaseSettings, SettingsConfigDict


class NotificationsSettings(BaseModel):
    retention_days: int | None = Field(default=None, ge=0)
    max_per_user: int | None = Field(default=None, ge=0)


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
        env_nested_delimiter="__",
    )

    api_contour: Literal["public", "admin", "ops", "all"] = Field(
        default="all",
        validation_alias=AliasChoices("API_CONTOUR", "APP_API_CONTOUR"),
    )

    @field_validator("database_url", mode="before")
    @classmethod
    def _normalize_database_url(cls, value: Any) -> Any:
        if value is None:
            return None
        try:
            return sanitize_async_dsn(str(value))
        except (ValueError, TypeError) as exc:
            logger.debug(
                "sanitize_async_dsn: database value normalisation failed", exc_info=exc
            )
            return value

    # base
    env: Literal["dev", "test", "prod"] = "dev"
    database_url: AnyUrl = Field(
        default=cast(AnyUrl, "postgresql://app:app@localhost:5432/app")
    )
    database_url_admin: AnyUrl | None = Field(
        default=None,
        validation_alias=AliasChoices("DATABASE_URL_ADMIN", "APP_DATABASE_URL_ADMIN"),
    )
    database_url_ops: AnyUrl | None = Field(
        default=None,
        validation_alias=AliasChoices("DATABASE_URL_OPS", "APP_DATABASE_URL_OPS"),
    )
    redis_url: AnyUrl = Field(default=cast(AnyUrl, "redis://localhost:6379/0"))
    home_cache_enabled: bool = Field(
        default=True,
        validation_alias=AliasChoices("HOME_CACHE_ENABLED", "APP_HOME_CACHE_ENABLED"),
    )
    home_cache_redis_url: AnyUrl | None = Field(
        default=None,
        validation_alias=AliasChoices("HOME_CACHE_REDIS_URL", "APP_HOME_CACHE_URL"),
    )
    home_cache_ttl: int = Field(
        default=300,
        validation_alias=AliasChoices("HOME_CACHE_TTL", "APP_HOME_CACHE_TTL"),
    )
    home_cache_key_prefix: str = Field(
        default="home:public",
        validation_alias=AliasChoices(
            "HOME_CACHE_KEY_PREFIX", "APP_HOME_CACHE_KEY_PREFIX"
        ),
    )
    database_allow_remote: bool = Field(
        default=False,
        validation_alias=AliasChoices(
            "DATABASE_ALLOW_REMOTE", "APP_DATABASE_ALLOW_REMOTE"
        ),
    )
    database_ssl_ca: str | None = Field(
        default=None,
        validation_alias=AliasChoices("DATABASE_SSL_CA", "APP_DATABASE_SSL_CA"),
    )

    # events platform
    event_topics: str = "profile.updated.v1"  # CSV
    event_group: str = "relay"
    event_rate_qps: int = 1000
    event_idempotency_ttl: int = 86400

    # notifications
    notify_topics: str | None = None  # CSV; if None, reuse event_topics
    notify_webhook_url: AnyUrl | None = None

    # telemetry / rum
    rum_rollup_interval_sec: float = Field(
        default=60.0,
        validation_alias=AliasChoices(
            "RUM_ROLLUP_INTERVAL_SEC", "APP_RUM_ROLLUP_INTERVAL_SEC"
        ),
    )
    rum_rollup_min_age_sec: float = Field(
        default=120.0,
        validation_alias=AliasChoices(
            "RUM_ROLLUP_MIN_AGE_SEC", "APP_RUM_ROLLUP_MIN_AGE_SEC"
        ),
    )
    rum_rollup_batch_size: int = Field(
        default=200,
        validation_alias=AliasChoices(
            "RUM_ROLLUP_BATCH_SIZE", "APP_RUM_ROLLUP_BATCH_SIZE"
        ),
    )
    rum_export_s3_bucket: str | None = Field(
        default=None,
        validation_alias=AliasChoices(
            "RUM_EXPORT_S3_BUCKET", "APP_RUM_EXPORT_S3_BUCKET"
        ),
    )
    rum_export_s3_prefix: str = Field(
        default="rum/rollup/",
        validation_alias=AliasChoices(
            "RUM_EXPORT_S3_PREFIX", "APP_RUM_EXPORT_S3_PREFIX"
        ),
    )
    rum_export_s3_region: str | None = Field(
        default=None,
        validation_alias=AliasChoices(
            "RUM_EXPORT_S3_REGION", "APP_RUM_EXPORT_S3_REGION"
        ),
    )
    rum_export_compress: bool = Field(
        default=True,
        validation_alias=AliasChoices("RUM_EXPORT_COMPRESS", "APP_RUM_EXPORT_COMPRESS"),
    )

    # SMTP (email notifications)
    smtp_mock: bool = True
    smtp_host: str | None = None
    smtp_port: int | None = 587
    smtp_username: str | None = None
    smtp_password: SecretStr | None = None
    smtp_tls: bool = True
    smtp_mail_from: str | None = None
    smtp_mail_from_name: str | None = None

    # auth/iam (stub defaults)
    auth_jwt_secret: SecretStr = Field(default=SecretStr("dev-secret-change-me"))
    auth_jwt_algorithm: str = Field(default="HS256")
    auth_jwt_expires_min: int = 15
    auth_jwt_refresh_expires_days: int = 7
    auth_csrf_cookie_name: str = Field(default="XSRF-TOKEN")
    auth_csrf_header_name: str = Field(default="X-CSRF-Token")
    auth_csrf_ttl_seconds: int | None = Field(default=None, ge=60, le=7200)
    auth_bootstrap_login: str | None = None
    auth_bootstrap_password: SecretStr | None = None
    auth_bootstrap_role: str = "admin"
    auth_bootstrap_user_id: str = "bootstrap-root"
    auth_bootstrap_enabled: bool = False
    cors_origins: str | None = None

    # admin/ops guard keys
    admin_api_key: SecretStr | None = Field(
        default=None,
        validation_alias=AliasChoices("ADMIN_API_KEY", "APP_ADMIN_API_KEY"),
    )
    ops_api_key: SecretStr | None = Field(
        default=None,
        validation_alias=AliasChoices("OPS_API_KEY", "APP_OPS_API_KEY"),
    )

    # search (in-memory only)
    search_persist_path: str | None = "apps/backend/var/search_index.json"

    # product feature flags (DDD-only)
    referrals_enabled: bool = True
    premium_enabled: bool = True
    achievements_enabled: bool = True
    worlds_enabled: bool = True
    nodes_cache_ttl_seconds: int = Field(
        default=300,
        validation_alias=AliasChoices("NODES_CACHE_TTL", "APP_NODES_CACHE_TTL"),
    )
    nodes_cache_max_entries: int = Field(
        default=5000,
        validation_alias=AliasChoices(
            "NODES_CACHE_MAX_ENTRIES", "APP_NODES_CACHE_MAX_ENTRIES"
        ),
    )

    # billing/webhook integration
    billing_webhook_secret: SecretStr | None = None

    embedding_provider: str | None = Field(
        default=None,
        validation_alias=AliasChoices("EMBEDDING_PROVIDER", "APP_EMBEDDING_PROVIDER"),
    )
    embedding_api_base: str | None = Field(
        default=None,
        validation_alias=AliasChoices("EMBEDDING_API_BASE", "APP_EMBEDDING_API_BASE"),
    )
    embedding_model: str | None = Field(
        default=None,
        validation_alias=AliasChoices("EMBEDDING_MODEL", "APP_EMBEDDING_MODEL"),
    )
    embedding_api_key: SecretStr | None = Field(
        default=None,
        validation_alias=AliasChoices("EMBEDDING_API_KEY", "APP_EMBEDDING_API_KEY"),
    )
    embedding_dim: int | None = Field(
        default=None,
        validation_alias=AliasChoices("EMBEDDING_DIM", "APP_EMBEDDING_DIM"),
    )
    embedding_enabled: bool = True
    embedding_timeout: float = Field(default=10.0)
    embedding_connect_timeout: float = Field(default=2.0)
    embedding_retries: int = 3

    enable_debug_routes: bool = False

    # normalize optional URL envs: empty string -> None
    @field_validator("notify_webhook_url", mode="before")
    @classmethod
    def _empty_url_to_none(cls, value: Any) -> Any:
        if value is None:
            return None
        try:
            text_value = str(value).strip()
        except (ValueError, TypeError) as exc:
            logger.debug("notify_webhook_url: normalisation failed", exc_info=exc)
            return value
        return value if text_value else None

    # experimental routers (can be disabled for cutover)
    nodes_enabled: bool = True
    tags_enabled: bool = True
    quests_enabled: bool = True
    navigation_enabled: bool = True
    content_enabled: bool = True
    ai_enabled: bool = True
    moderation_enabled: bool = True

    notifications: NotificationsSettings = Field(
        default_factory=NotificationsSettings,
    )

    def database_url_for_contour(self, contour: str | None = None) -> str:
        effective = (contour or getattr(self, "api_contour", "all") or "all").lower()
        if effective == "admin" and self.database_url_admin:
            return str(self.database_url_admin)
        if effective == "ops" and self.database_url_ops:
            return str(self.database_url_ops)
        if self.database_url:
            return str(self.database_url)
        return ""


def to_async_dsn(url: AnyUrl | str) -> str:
    return sanitize_async_dsn(url)


def load_settings() -> Settings:
    s = Settings()
    if s.env == "prod":
        # Primitive guard; extend as needed.
        if "localhost" in str(s.database_url):
            raise ValidationError("localhost database in prod", Settings)
        if not s.database_allow_remote:
            s.database_allow_remote = True
    return s

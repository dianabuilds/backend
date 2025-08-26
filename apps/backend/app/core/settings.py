import logging
import os
from enum import Enum
from functools import lru_cache
from pathlib import Path

from pydantic import AliasChoices, Field
from pydantic_settings import BaseSettings, SettingsConfigDict

from .app_settings import (
    AdminSettings,
    AuthSettings,
    CacheSettings,
    CompassSettings,
    CookieSettings,
    CsrfSettings,
    DatabaseSettings,
    EmbeddingSettings,
    JwtSettings,
    LoggingSettings,
    NavigationSettings,
    ObservabilitySettings,
    PaymentSettings,
    RateLimitSettings,
    RealIPSettings,
    SecuritySettings,
    SentrySettings,
    SMTPSettings,
)

logger = logging.getLogger(__name__)

BASE_DIR = Path(__file__).resolve().parents[2]


class ProjectSettings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=str(BASE_DIR / ".env") if (BASE_DIR / ".env").exists() else None,
        env_file_encoding="utf-8",
        case_sensitive=False,
        env_nested_delimiter="__",
        extra="ignore",
    )


class EnvMode(str, Enum):
    development = "development"
    test = "test"
    staging = "staging"
    production = "production"


_ENV_DEFAULTS: dict[EnvMode, dict[str, object]] = {
    EnvMode.development: {
        "allow_external_calls": True,
        "preview_default_mode": "preview",
        "rate_limit_policy": "lenient",
        "ai_provider": "mock",
        "payment_provider": "mock",
        "email_provider": "console",
        "rng_seed_strategy": "fixed",
    },
    EnvMode.test: {
        "allow_external_calls": True,
        "preview_default_mode": "preview",
        "rate_limit_policy": "lenient",
        "ai_provider": "mock",
        "payment_provider": "mock",
        "email_provider": "console",
        "rng_seed_strategy": "fixed",
    },
    EnvMode.staging: {
        "allow_external_calls": True,
        "preview_default_mode": "preview",
        "rate_limit_policy": "lenient",
        "ai_provider": "openai",
        "payment_provider": "stripe",
        "email_provider": "smtp",
        "rng_seed_strategy": "random",
    },
    EnvMode.production: {
        "allow_external_calls": False,
        "preview_default_mode": "disabled",
        "rate_limit_policy": "strict",
        "ai_provider": "openai",
        "payment_provider": "stripe",
        "email_provider": "smtp",
        "rng_seed_strategy": "random",
    },
}


class Settings(ProjectSettings):
    env_mode: EnvMode = Field(
        default=EnvMode.development,
        validation_alias=AliasChoices("APP_ENV_MODE", "ENVIRONMENT", "ENV_MODE"),
    )
    debug: bool = False

    allow_external_calls: bool | None = None
    preview_default_mode: str | None = None
    rate_limit_policy: str | None = None
    ai_provider: str | None = None
    payment_provider: str | None = None
    email_provider: str | None = None
    rng_seed_strategy: str | None = None

    # CORS settings
    cors_allow_credentials: bool = Field(
        default=True,
        validation_alias=AliasChoices(
            "APP_CORS_ALLOW_CREDENTIALS", "CORS_ALLOW_CREDENTIALS"
        ),
    )
    cors_allow_origins: list[str] = Field(
        default_factory=list,
        validation_alias=AliasChoices(
            "APP_CORS_ALLOW_ORIGINS",
            "CORS_ALLOW_ORIGINS",
            "CORS_ALLOWED_ORIGINS",
        ),
    )
    cors_allow_methods: list[str] = Field(
        default_factory=lambda: [
            "GET",
            "POST",
            "PUT",
            "DELETE",
            "OPTIONS",
            "PATCH",
        ],
        validation_alias=AliasChoices(
            "APP_CORS_ALLOW_METHODS",
            "CORS_ALLOW_METHODS",
            "CORS_ALLOWED_METHODS",
        ),
    )
    cors_allow_headers: list[str] = Field(
        default_factory=lambda: [
            "Authorization",
            "Content-Type",
            "X-CSRF-Token",
            "X-Requested-With",
        ],
        validation_alias=AliasChoices(
            "APP_CORS_ALLOW_HEADERS",
            "CORS_ALLOW_HEADERS",
            "CORS_ALLOWED_HEADERS",
        ),
    )
    cors_allow_origin_regex: str | None = Field(
        default=None,
        validation_alias=AliasChoices(
            "APP_CORS_ALLOW_ORIGIN_REGEX",
            "CORS_ALLOW_ORIGIN_REGEX",
        ),
    )
    cors_expose_headers: list[str] = Field(
        default_factory=list,
        validation_alias=AliasChoices(
            "APP_CORS_EXPOSE_HEADERS",
            "CORS_EXPOSE_HEADERS",
        ),
    )
    cors_max_age: int = Field(
        default=600,
        validation_alias=AliasChoices(
            "APP_CORS_MAX_AGE",
            "CORS_MAX_AGE",
        ),
    )

    # Async processing and related features
    async_enabled: bool = False
    queue_broker_url: str = ""
    idempotency_ttl_sec: int = 86400
    outbox_poll_interval_ms: int = 500
    coalesce_lock_ttl_ms: int = 2000

    database: DatabaseSettings = DatabaseSettings()
    cache: CacheSettings = CacheSettings()
    jwt: JwtSettings = JwtSettings()
    navigation: NavigationSettings = NavigationSettings()
    compass: CompassSettings = CompassSettings()
    embedding: EmbeddingSettings = EmbeddingSettings()
    admin: AdminSettings = AdminSettings()
    security: SecuritySettings = SecuritySettings()
    logging: LoggingSettings = LoggingSettings()
    smtp: SMTPSettings = SMTPSettings()
    sentry: SentrySettings = SentrySettings()
    payment: PaymentSettings = PaymentSettings()
    cookie: CookieSettings = CookieSettings()
    rate_limit: RateLimitSettings = RateLimitSettings()
    csrf: CsrfSettings = CsrfSettings()
    real_ip: RealIPSettings = RealIPSettings()
    observability: ObservabilitySettings = ObservabilitySettings()
    auth: AuthSettings = AuthSettings()

    def model_post_init(self, __context: dict) -> None:  # type: ignore[override]
        defaults = _ENV_DEFAULTS.get(self.env_mode, {})
        for field, value in defaults.items():
            if getattr(self, field) in (None, ""):
                setattr(self, field, value)

        # --- Redis URL normalization -------------------------------------------------
        # Берём REDIS_URL из окружения, если в секции cache пусто
        if self.cache.redis_url in (None, ""):
            self.cache.redis_url = os.getenv("REDIS_URL")

        # Если установлен REDIS_SSL/REDIS_TLS=true или порт указывает на TLS,
        # то принудительно переводим схему на rediss://
        def _normalize_redis_url(url: str | None) -> str | None:
            if not url:
                return url
            try:
                from urllib.parse import urlparse, urlunparse
                parsed = urlparse(url)
                tls_hint = os.getenv("REDIS_SSL") or os.getenv("REDIS_TLS")
                tls_enabled = str(tls_hint).lower() in {"1", "true", "yes", "on"}
                # Хостинговые TLS-порты часто 6380, 14403; redns/redislabs также обычно требуют TLS
                is_tls_port = (parsed.port in {6380, 14403, 443})
                host_hint = (parsed.hostname or "").lower()
                requires_tls = tls_enabled or is_tls_port or ("redis-cloud" in host_hint) or ("redns" in host_hint)
                if parsed.scheme == "redis" and requires_tls:
                    parsed = parsed._replace(scheme="rediss")
                    return urlunparse(parsed)
                return url
            except Exception:
                return url

        self.cache.redis_url = _normalize_redis_url(self.cache.redis_url)

        # Проталкиваем в другие подсистемы, если у них пусто; иначе тоже нормализуем
        if self.auth.redis_url in (None, ""):
            self.auth.redis_url = self.cache.redis_url
        else:
            self.auth.redis_url = _normalize_redis_url(self.auth.redis_url)

        if self.rate_limit.redis_url in (None, ""):
            self.rate_limit.redis_url = self.cache.redis_url
        else:
            self.rate_limit.redis_url = _normalize_redis_url(self.rate_limit.redis_url)

    @property
    def is_production(self) -> bool:
        return self.env_mode == EnvMode.production

    @property
    def database_url(self) -> str:
        """Return the database connection URL without modifying the name.

        Previously the environment suffix (e.g. ``_development``) was
        automatically appended to the database name. This caused connection
        attempts to non‑existent databases like ``defaultdb_development`` when
        the actual database was simply ``defaultdb``. Now we rely on the name
        provided in the settings as-is so the correct database is used.
        """
        return self.database.url

    @property
    def database_name(self) -> str:
        """Return the configured database name without environment suffix."""
        return self.database.name

    @property
    def db_connect_args(self) -> dict:
        return self.database.connect_args

    @property
    def db_pool_settings(self) -> dict:
        if self.is_production:
            return {
                "pool_size": self.database.pool_size * 2,
                "max_overflow": self.database.max_overflow * 2,
                "pool_timeout": self.database.pool_timeout,
                "pool_recycle": self.database.pool_recycle,
                "pool_pre_ping": True,
                "echo": False,
            }
        return {
            "pool_size": self.database.pool_size,
            "max_overflow": self.database.max_overflow,
            "pool_timeout": self.database.pool_timeout,
            "pool_recycle": self.database.pool_recycle,
            "pool_pre_ping": True,
            "echo": self.debug,
        }

    def effective_origins(self) -> dict[str, list[str] | str]:
        """Return kwargs for CORSMiddleware based on configuration."""
        if self.cors_allow_origins:
            result: dict[str, list[str] | str] = {"allow_origins": self.cors_allow_origins}
            if not self.is_production:
                # Разрешаем любые http-origin'ы в dev/test для удобства разработки
                result["allow_origin_regex"] = r"http://[^/]+"
            return result
        if self.is_production:
            return {"allow_origins": []}
        return {"allow_origin_regex": r"http://[^/]+"}


def validate_settings(settings: Settings) -> None:
    missing = []

    def _is_placeholder(value: str | None) -> bool:
        if value is None:
            return True
        return value == "" or "change_me" in value or "change-me" in value

    if _is_placeholder(settings.database.username):
        missing.append("DATABASE__USERNAME")
    if _is_placeholder(settings.database.password):
        missing.append("DATABASE__PASSWORD")
    if _is_placeholder(settings.database.host):
        missing.append("DATABASE__HOST")
    if _is_placeholder(settings.database.name):
        missing.append("DATABASE__NAME")

    if _is_placeholder(settings.jwt.secret):
        missing.append("JWT__SECRET")
    if settings.payment.jwt_secret:
        if _is_placeholder(settings.payment.jwt_secret):
            missing.append("PAYMENT__JWT_SECRET")
        if settings.payment.jwt_secret == settings.jwt.secret:
            missing.append("PAYMENT__JWT_SECRET distinct from JWT__SECRET")
    if settings.payment.webhook_secret and _is_placeholder(
        settings.payment.webhook_secret
    ):
        missing.append("PAYMENT__WEBHOOK_SECRET")

    if settings.async_enabled and _is_placeholder(settings.queue_broker_url):
        missing.append("QUEUE_BROKER_URL")

    if settings.embedding.name == "aimlapi":
        if not settings.embedding.api_base:
            missing.append("EMBEDDING_API_BASE")
        if not settings.embedding.api_key:
            missing.append("EMBEDDING_API_KEY")
        if not settings.embedding.model:
            missing.append("EMBEDDING_MODEL")

    if settings.is_production and (
        not settings.cors_allow_origins or "*" in settings.cors_allow_origins
    ):
        missing.append("APP_CORS_ALLOW_ORIGINS (must be explicit origins)")

    if missing:
        missing_vars = ", ".join(missing)
        logger.warning(f"Missing critical environment variables: {missing_vars}")
        if settings.is_production:
            raise ValueError(
                f"Missing critical environment variables in production: {missing_vars}"
            )


@lru_cache
def get_settings() -> Settings:
    settings = Settings()
    validate_settings(settings)
    return settings


settings = get_settings()

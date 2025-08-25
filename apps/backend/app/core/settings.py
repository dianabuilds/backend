from functools import lru_cache
from pathlib import Path
import logging
from enum import Enum
from pydantic_settings import BaseSettings, SettingsConfigDict

from .app_settings import (
    DatabaseSettings,
    CacheSettings,
    JwtSettings,
    NavigationSettings,
    CompassSettings,
    CorsSettings,
    EmbeddingSettings,
    AdminSettings,
    SecuritySettings,
    LoggingSettings,
    SMTPSettings,
    SentrySettings,
    PaymentSettings,
    CookieSettings,
    RateLimitSettings,
    CsrfSettings,
    RealIPSettings,
    ObservabilitySettings,
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
    env_mode: EnvMode = EnvMode.development
    debug: bool = False

    allow_external_calls: bool | None = None
    preview_default_mode: str | None = None
    rate_limit_policy: str | None = None
    ai_provider: str | None = None
    payment_provider: str | None = None
    email_provider: str | None = None
    rng_seed_strategy: str | None = None

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
    cors: CorsSettings = CorsSettings()
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

    def model_post_init(self, __context: dict) -> None:  # type: ignore[override]
        defaults = _ENV_DEFAULTS.get(self.env_mode, {})
        for field, value in defaults.items():
            if getattr(self, field) in (None, ""):
                setattr(self, field, value)

    @property
    def is_production(self) -> bool:
        return self.env_mode == EnvMode.production

    @property
    def database_url(self) -> str:
        db = self.database
        name = f"{db.name}_{self.env_mode.value}" if db.name else db.name
        return (
            f"postgresql+asyncpg://{db.username}:{db.password}"
            f"@{db.host}:{db.port}/{name}"
        )

    @property
    def database_name(self) -> str:
        return f"{self.database.name}_{self.env_mode.value}" if self.database.name else self.database.name

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
        not settings.cors.allowed_origins or "*" in settings.cors.allowed_origins
    ):
        missing.append("CORS_ALLOWED_ORIGINS (must be explicit origins)")

    if missing:
        missing_vars = ", ".join(missing)
        logger.warning(f"Missing critical environment variables: {missing_vars}")
        if settings.is_production:
            raise ValueError(
                f"Missing critical environment variables in production: {missing_vars}"
            )


@lru_cache()
def get_settings() -> Settings:
    settings = Settings()
    validate_settings(settings)
    return settings


settings = get_settings()

from functools import lru_cache
from pathlib import Path
import logging
from pydantic_settings import BaseSettings, SettingsConfigDict

from .settings import (
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
)

logger = logging.getLogger(__name__)

BASE_DIR = Path(__file__).resolve().parents[2]


class ProjectSettings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=str(BASE_DIR / ".env") if (BASE_DIR / ".env").exists() else None,
        env_file_encoding="utf-8",
        case_sensitive=False,
    )


class Settings(ProjectSettings):
    environment: str = "development"  # development, staging, production
    debug: bool = False

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

    @property
    def is_production(self) -> bool:
        return self.environment.lower() == "production"

    @property
    def database_url(self) -> str:
        return self.database.url

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
    if not settings.database.username:
        missing.append("DB_USERNAME")
    if not settings.database.password:
        missing.append("DB_PASSWORD")
    if not settings.database.host:
        missing.append("DB_HOST")
    if not settings.database.name:
        missing.append("DB_NAME")

    if not settings.jwt.secret or settings.jwt.secret == "change-me-in-production":
        missing.append("JWT_SECRET")

    if settings.embedding.name == "aimlapi":
        if not settings.embedding.api_base:
            missing.append("EMBEDDING_API_BASE")
        if not settings.embedding.api_key:
            missing.append("EMBEDDING_API_KEY")
        if not settings.embedding.model:
            missing.append("EMBEDDING_MODEL")

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

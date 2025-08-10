from functools import lru_cache
from pydantic_settings import BaseSettings, SettingsConfigDict
import os
import logging
from pathlib import Path

logger = logging.getLogger(__name__)

# Абсолютный путь к .env в корне проекта: app/core/config.py -> app/core -> app -> проект
ENV_PATH = Path(__file__).resolve().parents[2] / ".env"

class Settings(BaseSettings):
    # Общие настройки
    ENVIRONMENT: str = "development"  # development, staging, production
    DEBUG: bool = False

    # Database settings
    db_username: str = ""
    db_password: str = ""
    db_host: str = ""
    db_port: int = 5432
    db_name: str = ""
    db_sslmode: str = "require"

    # Настройки пула соединений
    db_pool_size: int = 5
    db_max_overflow: int = 10
    db_pool_timeout: int = 30
    db_pool_recycle: int = 1800
    db_echo: bool = False

    # JWT settings
    jwt_secret: str = "test-secret"
    jwt_algorithm: str = "HS256"
    jwt_expiration: int = 60 * 60  # seconds

    # AI/Embedding settings
    # backend: simple | aimlapi (в дальнейшем можно добавить другие значения)
    embedding_backend: str = "simple"
    embedding_model: str = ""
    embedding_dim: int = 384
    embedding_api_base: str = ""
    embedding_api_key: str = ""

    # CORS settings
    cors_allowed_origins: list[str] = ["http://localhost:5173", "http://127.0.0.1:5173"]
    cors_allow_credentials: bool = True
    cors_allowed_methods: list[str] = ["*"]
    cors_allowed_headers: list[str] = ["*"]

    # Admin bootstrap (создание/исправление дефолтного администратора в dev)
    admin_bootstrap_enabled: bool = True
    admin_username: str = "admin"
    admin_email: str = "admin@example.com"
    admin_password: str = "admin123"

    # Security settings
    min_password_length: int = 3  # Минимальная длина пароля
    secure_password_policy: bool = False  # Строгая политика паролей (требование букв, цифр и т.д.)

    # Cache settings
    redis_url: str | None = None
    navigation_ttl_hours: int = 2
    navigation_max_options: int = 3
    navigation_weight_compass: float = 0.5
    navigation_weight_echo: float = 0.3
    navigation_weight_random: float = 0.2

    # Compass / recommendation settings
    compass_top_k_db: int = 200
    compass_top_k_result: int = 20
    compass_pgv_probes: int = 10

    @property
    def database_url(self) -> str:
        """Создает URL для подключения к базе данных"""
        return (
            f"postgresql+asyncpg://{self.db_username}:{self.db_password}"
            f"@{self.db_host}:{self.db_port}/{self.db_name}"
        )

    @property
    def db_connect_args(self) -> dict:
        """Дополнительные аргументы для подключения к базе данных"""
        args = {}

        # Настройка SSL
        if self.db_sslmode == "require":
            args["ssl"] = True

        return args

    @property
    def is_production(self) -> bool:
        """Проверяет, является ли текущая среда продакшеном"""
        return self.ENVIRONMENT.lower() == "production"

    @property
    def db_pool_settings(self) -> dict:
        """Возвращает настройки пула соединений для текущей среды"""
        # В продакшен-среде увеличиваем размер пула
        if self.is_production:
            return {
                "pool_size": self.db_pool_size * 2,
                "max_overflow": self.db_max_overflow * 2,
                "pool_timeout": self.db_pool_timeout,
                "pool_recycle": self.db_pool_recycle,
                "pool_pre_ping": True,
                "echo": False,
            }

        return {
            "pool_size": self.db_pool_size,
            "max_overflow": self.db_max_overflow,
            "pool_timeout": self.db_pool_timeout,
            "pool_recycle": self.db_pool_recycle,
            "pool_pre_ping": True,
            "echo": self.DEBUG,
        }

    model_config = SettingsConfigDict(
        env_file=str(ENV_PATH) if ENV_PATH.exists() else None,
        env_file_encoding="utf-8",
        case_sensitive=False
    )


def validate_settings(settings: Settings) -> None:
    """Проверяет наличие всех необходимых настроек"""
    missing = []

    if not settings.db_username:
        missing.append("db_username")
    if not settings.db_password:
        missing.append("db_password")
    if not settings.db_host:
        missing.append("db_host")
    if not settings.db_name:
        missing.append("db_name")

    if not settings.jwt_secret or settings.jwt_secret == "change-me-in-production":
        missing.append("jwt_secret")

    # Проверяем обязательные переменные для внешнего провайдера эмбеддингов
    if settings.embedding_backend.lower() == "aimlapi":
        if not settings.embedding_api_base:
            missing.append("embedding_api_base")
        if not settings.embedding_api_key:
            missing.append("embedding_api_key")
        if not settings.embedding_model:
            missing.append("embedding_model")

    if missing:
        missing_vars = ", ".join(missing)
        logger.warning(f"Missing critical environment variables: {missing_vars}")

        if settings.is_production:
            raise ValueError(f"Missing critical environment variables in production: {missing_vars}")


@lru_cache()
def get_settings() -> Settings:
    """Возвращает экземпляр настроек с кэшированием для оптимизации"""
    settings = Settings()
    validate_settings(settings)
    return settings


settings = get_settings()

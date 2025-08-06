from functools import lru_cache
from pydantic_settings import BaseSettings, SettingsConfigDict
import os
import logging

logger = logging.getLogger(__name__)

class Settings(BaseSettings):
    # Общие настройки
    ENVIRONMENT: str = "development"  # development, staging, production
    DEBUG: bool = False

    # Database settings
    db_username: str
    db_password: str
    db_host: str
    db_port: int
    db_name: str
    db_sslmode: str = "require"

    # Настройки пула соединений
    db_pool_size: int = 5
    db_max_overflow: int = 10
    db_pool_timeout: int = 30
    db_pool_recycle: int = 1800
    db_echo: bool = False

    # JWT settings
    jwt_secret: str
    jwt_algorithm: str = "HS256"
    jwt_expiration: int = 60 * 60  # seconds

    # Security settings
    min_password_length: int = 3  # Минимальная длина пароля
    secure_password_policy: bool = False  # Строгая политика паролей (требование букв, цифр и т.д.)

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
        env_file=".env" if os.path.exists(".env") else None,
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

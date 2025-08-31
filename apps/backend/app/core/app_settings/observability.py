from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class ObservabilitySettings(BaseSettings):
    """Settings controlling observability features."""

    health_enabled: bool = Field(True, alias="OBS_HEALTH_ENABLED")
    db_check_timeout_ms: int = Field(500, alias="OBS_DB_CHECK_TIMEOUT_MS")
    redis_check_timeout_ms: int = Field(500, alias="OBS_REDIS_CHECK_TIMEOUT_MS")
    queue_check_timeout_ms: int = Field(500, alias="OBS_QUEUE_CHECK_TIMEOUT_MS")
    # Реальная векторизация может занимать > 500 мс — берём более реалистичный дефолт
    ai_check_timeout_ms: int = Field(3000, alias="OBS_AI_CHECK_TIMEOUT_MS")
    payment_check_timeout_ms: int = Field(500, alias="OBS_PAYMENT_CHECK_TIMEOUT_MS")

    structured_logs: bool = Field(True, alias="OBS_STRUCTURED_LOGS")
    log_level: str = Field("INFO", alias="OBS_LOG_LEVEL")
    include_correlation_id: bool = Field(True, alias="OBS_INCLUDE_CORRELATION_ID")

    metrics_enabled: bool = Field(True, alias="OBS_METRICS_ENABLED")
    metrics_path: str = Field("/metrics", alias="OBS_METRICS_PATH")
    metrics_auth_disabled: bool = Field(True, alias="OBS_METRICS_AUTH_DISABLED")

    ws_metrics_enabled: bool = Field(True, alias="OBS_WS_METRICS_ENABLED")

    model_config = SettingsConfigDict(extra="ignore")

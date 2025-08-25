from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class LoggingSettings(BaseSettings):
    level: str = Field("INFO", alias="LOG_LEVEL")
    request_level: str = Field("INFO", alias="REQUEST_LOG_LEVEL")
    slow_query_ms: int = Field(200, alias="SLOW_QUERY_MS")

    json_logs: bool = Field(False, alias="LOG_JSON")
    include_traceback: bool = Field(True, alias="LOG_INCLUDE_TRACEBACK")
    requests: bool = Field(True, alias="LOG_REQUESTS")
    slow_request_ms: int = Field(800, alias="LOG_SLOW_REQUEST_MS")
    file_enabled: bool = Field(False, alias="LOG_FILE_ENABLED")
    file_path: str = Field("logs/app.log", alias="LOG_FILE_PATH")
    file_rotate_bytes: int = Field(10_000_000, alias="LOG_FILE_ROTATE_BYTES")
    file_backup_count: int = Field(5, alias="LOG_FILE_BACKUP_COUNT")
    sampling_rate_debug: float = Field(0.0, alias="LOG_SAMPLING_RATE_DEBUG")
    service_name: str = Field("backend", alias="SERVICE_NAME")

    model_config = SettingsConfigDict(extra="ignore")


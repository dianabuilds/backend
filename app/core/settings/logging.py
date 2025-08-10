from pydantic_settings import BaseSettings, SettingsConfigDict


class LoggingSettings(BaseSettings):
    level: str = "INFO"
    json: bool = False
    include_traceback: bool = True
    requests: bool = True
    slow_request_ms: int = 800
    file_enabled: bool = False
    file_path: str = "logs/app.log"
    file_rotate_bytes: int = 10_000_000
    file_backup_count: int = 5
    sampling_rate_debug: float = 0.0
    service_name: str = "backend"

    model_config = SettingsConfigDict(env_prefix="LOG_")


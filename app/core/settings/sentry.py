from pydantic import Field
from pydantic_settings import BaseSettings


class SentrySettings(BaseSettings):
    enabled: bool = True
    dsn: str | None = None
    env: str | None = Field(default=None, alias="ENV")
    traces_sample_rate: float = 0.0

    model_config = {
        "env_prefix": "SENTRY_",
        "extra": "ignore",
    }

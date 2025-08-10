from pydantic_settings import BaseSettings


class SentrySettings(BaseSettings):
    dsn: str | None = None
    traces_sample_rate: float = 0.0

    model_config = {
        "env_prefix": "SENTRY_",
        "extra": "ignore",
    }

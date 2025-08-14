from typing import List
from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class RealIPSettings(BaseSettings):
    enabled: bool = False
    trusted_proxies: List[str] = Field(default_factory=list)
    header: str = "X-Forwarded-For"
    depth: int | None = None

    model_config = SettingsConfigDict(env_prefix="REAL_IP_")

    @field_validator("trusted_proxies", mode="before")
    def split_csv(cls, v):  # noqa: N805
        if isinstance(v, str):
            return [item.strip() for item in v.split(",") if item.strip()]
        return v

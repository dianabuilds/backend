from __future__ import annotations

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class RealIPSettings(BaseSettings):
    enabled: bool = False
    trusted_proxies: list[str] = Field(default_factory=list)
    header: str = "X-Forwarded-For"
    depth: int | None = None

    model_config = SettingsConfigDict(env_prefix="REAL_IP_")

    @field_validator("trusted_proxies", mode="before")
    def split_csv(cls, v):  # noqa: N805
        if isinstance(v, str):
            return [item.strip() for item in v.split(",") if item.strip()]
        return v

    @field_validator("depth", mode="before")
    def empty_depth_as_none(cls, v):  # noqa: N805
        if v is None:
            return None
        if isinstance(v, str) and v.strip() == "":
            return None
        return v


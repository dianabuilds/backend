from pydantic_settings import BaseSettings, SettingsConfigDict
from typing import List

class CorsSettings(BaseSettings):
    allowed_origins: List[str] = ["http://localhost:5173", "http://127.0.0.1:5173"]
    allow_credentials: bool = True
    allowed_methods: List[str] = ["*"]
    allowed_headers: List[str] = ["*"]

    model_config = SettingsConfigDict(env_prefix="CORS_")

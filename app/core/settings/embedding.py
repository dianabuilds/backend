from pydantic_settings import BaseSettings, SettingsConfigDict

class EmbeddingSettings(BaseSettings):
    backend: str = "simple"
    model: str = ""
    dim: int = 384
    api_base: str = ""
    api_key: str = ""

    model_config = SettingsConfigDict(env_prefix="EMBEDDING_")
